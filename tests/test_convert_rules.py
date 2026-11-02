from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import pymupdf

from convert_rules import (
    SOURCE, SYMBOLS, TEXT_FLAGS, FIGURES, STOP_SECTION, COMPOSITE_FIGURES, FIGURE_GROUPS,
    APPENDIX_SECTION, APPENDIX_CARDS, organize,
    convert, extract_blocks, inline_text, translated, html_document, WEB, figure_content, Block, render_blocks,
)
from pdf_artwork import isolate_figure


def plain_text(markdown):
    markdown = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', markdown)
    markdown = re.sub(r'\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\([^)]+\)', r'\1', markdown)
    return markdown.replace('**', '').replace('*', '')


class HtmlContent(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == 'i':
            self.text.append('[' + attrs['aria-label'] + ']')

    def handle_data(self, data):
        self.text.append(data)


class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.output = Path(cls.directory.name) / 'converted'
        cls.index = convert(SOURCE, cls.output)
        cls.root = cls.output
        cls.output = cls.output / 'markdown'
        cls.files = {p.relative_to(cls.output).as_posix(): p.read_text(encoding='utf-8')
                     for p in cls.output.rglob('*.md')}
        cls.text = '\n'.join(cls.files.values())

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def rule(self, name, section='glossary'):
        return self.files[f'{section}/{section}-{name}.md']

    def test_index_sections_descriptions_and_every_rule(self):
        index = self.files['index.md']
        self.assertEqual(re.findall(r'^## .+$', index, re.M), ['## Introduction', '## Glossary', '## Appendix'])
        self.assertIn('The glossary lists all gameplay terms and phases in detail.', index)
        self.assertIn('This reference is the definitive source', index)
        self.assertLess(index.index('## Introduction'), index.index('introduction-golden-rules.md'))
        self.assertLess(index.index('## Glossary'), index.index('glossary-abilities.md'))
        links = re.findall(r'\]\(([^)]+\.md)\)', index)
        self.assertEqual(len(links), 179)
        self.assertEqual(set(links), set(self.files) - {'index.md'})
        self.assertEqual(sum(p.startswith('introduction/') for p in links), 3)
        self.assertEqual(sum(p.startswith('glossary/') for p in links), 149)
        for link in links:
            folder, filename = link.split('/')
            self.assertRegex(filename, '^' + folder + r'-[a-z0-9]+(?:-[a-z0-9]+)*\.md$')
            self.assertEqual(len(re.findall(r'^# ', self.files[link], re.M)), 1)

    def test_appendix_index_groups_in_both_formats(self):
        expected = [
            ('Examples', ['extended-examples']),
            ('Objects: Bombs and Mines', ['bomblet', 'concussion-bomb', 'electro-proton-bomb',
                                        'cluster-mine', 'conner-net', 'ion-bomb', 'proton-bomb',
                                        'seismic-charge', 'proximity-mine', 'thermal-detonator', 'blazer-bomb']),
            ('Objects: Obstacles', ['asteroids', 'debris-clouds', 'loose-cargo', 'cargo-drift',
                                   'gas-clouds', 'spare-parts']),
            ('Objects: Remotes', ['buzz-droid-swarm', 'sensor-buoy', 'dark-eye-probe-droid', 'commando-team']),
            ('Device and Deploying Examples', ['deploy-example', 'dropping-bomb-example', 'launching-bomb-example']),
            ('Card Anatomies', ['ship-cards', 'upgrade-cards']),
        ]
        index = self.files['index.md']
        sections = re.split(r'^### (.+)\n', index, flags=re.M)
        self.assertEqual(sections[1::2], [title for title, _ in expected])
        for content, (_, names) in zip(sections[2::2], expected, strict=True):
            links = re.findall(r'appendix-examples/appendix-examples-([^()]+)\.md', content)
            self.assertEqual(links, names)
        html = (self.root / 'docs/index.html').read_text()
        self.assertEqual(re.findall(r'<h3>([^<]+)</h3>', html), [title for title, _ in expected])
        sections = re.split(r'<h3>[^<]+</h3>', html)
        for content, (_, names) in zip(sections[1:], expected, strict=True):
            links = re.findall(r'appendix-examples/appendix-examples-([^"<>]+)\.html', content)
            self.assertEqual(links, names)

    def test_boundary_includes_examples_and_skips_later_sections(self):
        self.assertNotIn("# " + STOP_SECTION + "\n", self.text)
        self.assertIn("## Appendix\n", self.text)
        self.assertIn('Ability Queue Example #1', self.text)
        self.assertNotIn('SAW’S RENEGADES', self.text)
        self.assertNotIn('Lucasfilm', self.text)
        with pymupdf.open(SOURCE) as document:
            blocks = extract_blocks(document)
        self.assertEqual(min(b.page for b in blocks), 2)
        self.assertEqual(max(b.page for b in blocks), 29)
        self.assertEqual([b.text for b in blocks if b.kind == 'section'], ['INTRODUCTION', 'GLOSSARY', APPENDIX_SECTION])

    def test_appendix_cards_and_examples_are_individually_indexed(self):
        appendix = 'appendix-examples'
        self.assertEqual(sum(p.startswith(appendix + '/') for p in self.files), 27)
        with pymupdf.open(SOURCE) as document:
            for number, cards in APPENDIX_CARDS.items():
                for title, bounds in cards:
                    name = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                    text = self.rule(name, appendix)
                    self.assertTrue(text.startswith('# ' + title + '\n'))
                    self.assertIn(f'[{title}]({appendix}/{appendix}-{name}.md)', self.files['index.md'])
                    if number == 29:
                        continue
                    rendered = re.sub(r'\s', '', plain_text(text))
                    for block in document[number - 1].get_text('dict', flags=TEXT_FLAGS)['blocks']:
                        for line in block.get('lines', []):
                            rect = pymupdf.Rect(line['bbox'])
                            if not pymupdf.Rect(bounds).contains((rect.tl + rect.br) / 2):
                                continue
                            if not any(s['font'] == 'EurostileLTStd-Cn' and 7.5 <= s['size'] <= 8.6
                                       for s in line['spans']):
                                continue
                            source = ''.join(translated(s) for s in line['spans'])
                            self.assertIn(re.sub(r'\s', '', source), rendered, (number, title, source))
        commando = self.rule('commando-team', appendix)
        self.assertIn('range 0. Your primary attack', plain_text(commando))
        self.assertIn('\n\n**Activation Phase:**', commando)
        self.assertIn('\n\nAt the end', self.rule('bomblet', appendix))
        for name, caption in [('deploy-example', 'The Phantom II deploys'),
                              ('dropping-bomb-example', 'This HWK-290 drops'),
                              ('launching-bomb-example', 'This TIE punisher launches')]:
            self.assertIn(caption, plain_text(self.rule(name, appendix)))
        for name in ('ship-cards', 'upgrade-cards'):
            self.assertEqual(self.rule(name, appendix).count('!['), 1)
        # Glossary rules retain ownership of existing links when an object shares its title.
        with pymupdf.open(SOURCE) as document:
            _, targets = organize(extract_blocks(document), self.output)
        self.assertEqual(targets['upgrade cards'].name, 'glossary-upgrade-cards.md')

    def test_appendix_composite_artwork_preserves_labels_and_annotations(self):
        with pymupdf.open(SOURCE) as document:
            for number, description in sorted(COMPOSITE_FIGURES):
                if number < 24:
                    continue
                box = next(box for box, name, _ in FIGURES[number] if name == description)
                with isolate_figure(document, number, FIGURE_GROUPS[number, description], box, unmarked=(number == 24)) as isolated:
                    clip = pymupdf.Rect(box)
                    original = document[number - 1].get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=clip)
                    artwork = isolated[0].get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=clip, alpha=True)
                    # Compare opaque artwork; transparent shadows blend against the removed card background.
                    source, pixels = original.samples, artwork.samples
                    difference = checked = 0
                    for index in range(artwork.width * artwork.height):
                        if pixels[index * 4 + 3] != 255:
                            continue
                        difference += sum(abs(source[index * 3 + channel] - pixels[index * 4 + channel])
                                          for channel in range(3))
                        checked += 3
                    self.assertGreater(checked, 100, description)
                    self.assertLess(difference / checked, 1, description)
                    if 'anatomy' in description:
                        self.assertEqual(isolated[0].get_text().split(),
                                         document[number - 1].get_text(clip=clip).split())

    def test_page_two_structure_and_paragraphs(self):
        golden = self.rule('golden-rules', 'introduction').split('\n\n')[1:]
        self.assertEqual(len(golden), 4)
        self.assertEqual(golden[0], 'If a rule in this guide contradicts the Rulebook, the rule in this guide takes precedence.')
        card = self.rule('card-interpretation', 'introduction')
        self.assertEqual(re.findall(r'^## .+$', card, re.M), [
            '## Use of “You”', '## Use of “May,” “Can,” and “Must”',
            '## Once Per Opportunity', '## And/Or',
        ])
        abilities = self.rule('abilities')
        replacement = abilities.split('## Replacement Effects\n\n')[1].split('## Paying Costs')[0]
        self.assertEqual(len(re.findall(r'^- ', replacement, re.M)), 3)
        self.assertEqual(len(re.findall(r'^    - ', replacement, re.M)), 2)
        self.assertIn('[ability queue](glossary-ability-queue.md)', abilities)
        self.assertIn('[destroyed](glossary-destroying-ships.md)', abilities)

    def test_continuations_and_lettered_and_numbered_lists(self):
        dock = plain_text(self.rule('dock'))
        self.assertIn('A docked ship performs an emergency deploy similar to deploying', dock)
        bearing = plain_text(self.rule('bearing'))
        self.assertIn('Reverse bank maneuvers are reverse maneuvers, not forward maneuvers.', bearing)
        self.assertIn('template (such as barrel rolling or boosting).', plain_text(self.rule('move')))
        attack = self.rule('attack')
        self.assertIn('    - **a.** **Measure Range:**', attack)
        self.assertIn('6. **Aftermath:**', attack)
        self.assertIn('The player with the most [critical-hit] results', self.rule('setup'))
        self.assertIn('6. **Prepare Other Components:**', self.rule('setup'))
        remotes = plain_text(self.rule('remotes'))
        self.assertIn('- If a remote would be relocated such that any part of it is outside of the play area, it flees', remotes)
        self.assertIn('non-purple maneuvers', self.rule('difficulty'))
        self.assertIn('Pilots can reinforce to angle their deflector shields and increase',
                      plain_text(self.rule('reinforce')))

    def test_attack_hit_miss_paragraph_stays_inside_step_four(self):
        attack = self.rule('attack')
        step = attack.split('4. **Neutralize Results:**')[1].split('5. **Deal Damage:**')[0]
        paragraph = ('    The attack [hits](glossary-hit.md) if at least one [hit] or '
                     '[critical-hit] result remains uncanceled; otherwise, '
                     'the attack [misses](glossary-miss.md).')
        self.assertIn('\n\n' + paragraph + '\n\n', step)
        self.assertLess(step.index('    - **b.**'), step.index(paragraph))
        self.assertNotIn('\n    Ships can perform attacks', attack)

    def test_tractor_boost_bullet_ends_before_next_page_paragraph(self):
        paragraphs = self.rule('tractor').split('\n\n')
        self.assertIn('- Perform a [boost](glossary-boost.md) using the [1 [straight]] maneuver template.', paragraphs)
        following = next(p for p in paragraphs if p.startswith('This move cannot cause'))
        self.assertTrue(following.endswith('the ship gains one stress token.'))

    def test_all_body_text_lines_survive_extraction(self):
        # Compare every source body line independently of converter paragraph/crop decisions.
        rendered = re.sub(r'\s', '', plain_text(self.text))
        checked = 0
        with pymupdf.open(SOURCE) as document:
            for page in list(document)[1:23]:
                for block in page.get_text('dict', flags=TEXT_FLAGS)['blocks']:
                    for line in block.get('lines', []):
                        if not any(s['font'] == 'EurostileLTStd-Cn' and 8.2 <= s['size'] <= 8.6
                                   for s in line['spans']):
                            continue
                        text = ''.join(translated(s) for s in line['spans']).strip()
                        text = re.sub(r'^([•◊]|[a-z]\.|\d+\.)\s*', '', text)
                        text = re.sub(r'\s', '', text)
                        if text:
                            checked += 1
                            self.assertIn(text, rendered, f'Lost source text on page {page.number + 1}: {text}')
        self.assertEqual(checked, 1917)

    def test_all_links_images_and_anchors_resolve(self):
        links = 0
        for name, text in self.files.items():
            for url in re.findall(r'\]\(([^)\n]+)\)', text):
                path, _, anchor = unquote(url).partition('#')
                target = (self.output / name).parent / path
                self.assertTrue(target.is_file(), f'{name}: broken link {url}')
                if anchor and target.suffix == '.md':
                    self.assertIn(f'<a id="{anchor}"></a>', target.read_text(encoding='utf-8'))
                links += 1
        self.assertGreater(links, 626)
        self.assertIn('../index.md#appendix-examples', self.rule('ability-queue'))
        self.assertIn('../index.md#appendix-examples', self.rule('device'))
        self.assertIn('glossary-charges.md#force-charge', self.rule('setup'))

    def test_symbols_and_composite_artwork(self):
        self.assertFalse(any(0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c) <= 0x10FFFD
                             or ord(c) < 32 and c not in '\n\t' for c in self.text))
        self.assertNotIn('\ufffc', self.text)
        self.assertIn('[barrel-roll]', self.rule('card-interpretation', 'introduction'))
        self.assertIn('[hyperdrive] Hyperdrive', self.rule('upgrade-icons'))
        images = list((self.output / 'assets').glob('*.png'))
        self.assertEqual(len(images), sum(len(figures) for figures in FIGURES.values()))
        illustration = self.output / 'assets/page-02-pilot-and-ship-abilities.png'
        image = pymupdf.Pixmap(illustration)
        self.assertTrue(image.alpha)
        abilities = self.rule('abilities')
        self.assertLess(abilities.index('## Pilot and Ship Abilities'), abilities.index('![Pilot and ship abilities]'))
        self.assertLess(abilities.index('![Pilot and ship abilities]'), abilities.index('## Replacement Effects'))
        self.assertNotIn('After you perform an action', abilities)

    def test_all_artwork_uses_transparent_object_groups(self):
        expected = {(page, name) for page, figures in FIGURES.items() for _, name, _ in figures}
        self.assertEqual(set(FIGURE_GROUPS), expected)
        for page, name in FIGURE_GROUPS:
            filename = f'page-{page:02d}-' + name.lower().replace(' ', '-') + '.png'
            pixmap = pymupdf.Pixmap(self.output / 'assets' / filename)
            self.assertTrue(pixmap.alpha, name)
            alpha = pixmap.samples[3::4]
            self.assertEqual(min(alpha), 0, name)
            self.assertGreater(max(alpha), 0, name)
        with pymupdf.open(SOURCE) as document:
            with isolate_figure(document, 3, (296,)) as isolated:
                self.assertEqual(isolated[0].get_text().strip(), '2')
            box = FIGURES[21][0][0]
            with isolate_figure(document, 21, FIGURE_GROUPS[21, 'Bank compared with sideslip'], box) as isolated:
                original = document[20].get_pixmap()
                artwork = isolated[0].get_pixmap()
                # This arrow is tagged as a layout Artifact, outside the Figure groups.
                checked = 0
                for y in range(163, 212):
                    for x in range(124, 224):
                        if original.pixel(x, y) == (0, 174, 239):
                            # Allow minor blending changes where the arrow crosses artwork.
                            self.assertLessEqual(max(abs(a - b) for a, b in zip(
                                artwork.pixel(x, y), original.pixel(x, y))), 5)
                            checked += 1
                self.assertGreater(checked, 60)
            box = FIGURES[20][1][0]
            with isolate_figure(document, 20, FIGURE_GROUPS[20, 'Correct and incorrect sideslip placement'], box) as isolated:
                self.assertEqual(isolated[0].get_text().split(), ['✓', '✘'])
            box, name, _ = FIGURES[23][0]
            _, captions = figure_content(document[22], box, name)
            with isolate_figure(document, 23, FIGURE_GROUPS[23, name], box,
                                [s['bbox'] for spans in captions for s in spans]) as isolated:
                self.assertEqual(isolated[0].get_text().strip(), '')

    def test_missing_figure_group_preserves_previous_output(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch.dict(FIGURE_GROUPS, {(3, 'Agility value on a ship card'): (-1,)}):
            with self.assertRaisesRegex(ValueError, 'Expected one Figure MCID -1'):
                convert(SOURCE, self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_captions_are_text_below_graphics_in_both_formats(self):
        ion = self.rule('ion')
        self.assertEqual(ion.count('\n\n*Ion Token*\n\n'), 1)
        self.assertLess(ion.index('![Ion token]'), ion.index('\n\n*Ion Token*'))
        barrel = self.rule('barrel-roll')
        self.assertIn('A TIE fighter barrel rolls to the right and slightly forward, slightly backward, or straight across.', barrel)
        sideslip = self.rule('sideslip')
        self.assertIn('Correct [2 [bank-left]] Sideslip', sideslip)
        self.assertIn('Incorrect [2 [bank-left]] Sideslip', sideslip)
        self.assertIn("The sideslip changes the **placement** of the template, but the template's is **not** flipped over to the opposite direction.", sideslip)
        range_text = self.rule('range')
        self.assertIn('The TIE fighter is **within** range 1 of the X-wing.', range_text)
        self.assertIn('The TIE fighter is **beyond** range 1 of the X-wing.', range_text)
        html = (self.root / 'docs/glossary/glossary-ion.html').read_text()
        self.assertRegex(html, r'<figure[^>]*><img [^>]+><figcaption><p>Ion Token</p></figcaption></figure>')
        html = (self.root / 'docs/glossary/glossary-primary-weapon.html').read_text()
        self.assertIn('<figcaption>', html)
        self.assertIn('aria-label="front-arc"', html)
        with pymupdf.open(SOURCE) as document:
            rendered = re.sub(r'\s', '', plain_text(self.text))
            for number, figures in FIGURES.items():
                for box, description, _ in figures:
                    if (number, description) in COMPOSITE_FIGURES:
                        continue
                    for line in document[number - 1].get_text('dict', flags=TEXT_FLAGS)['blocks']:
                        for line in line.get('lines', []):
                            rect = pymupdf.Rect(line['bbox'])
                            if (pymupdf.Rect(box).contains((rect.tl + rect.br) / 2)
                                    and any(s['font'] == 'EurostileLTStd-Cn' and 7 <= s['size'] <= 8.1
                                            for s in line['spans'])):
                                text = ''.join(translated(s) for s in line['spans'])
                                self.assertIn(re.sub(r'\s', '', text), rendered, (number, description))

    def test_callout_diagrams_keep_embedded_text_without_page_content(self):
        self.assertTrue({(2, 'Pilot and ship abilities'),
                         (4, 'Single turret arc indicator and ID tokens')} <= COMPOSITE_FIGURES)
        with pymupdf.open(SOURCE) as document:
            for number, description in sorted(COMPOSITE_FIGURES):
                if number >= 24:
                    continue
                box = next(box for box, name, _ in FIGURES[number] if name == description)
                with isolate_figure(document, number, FIGURE_GROUPS[number, description], box, unmarked=(number == 24)) as isolated:
                    self.assertEqual(isolated[0].get_text().split(),
                                     document[number - 1].get_text(clip=pymupdf.Rect(box)).split())
                    clip = pymupdf.Rect(box)
                    original = document[number - 1].get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=clip)
                    artwork = isolated[0].get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=clip)
                    # Isolated transparency can change antialiasing at object edges.
                    difference = sum(abs(a - b) for a, b in zip(original.samples, artwork.samples))
                    self.assertLess(difference / len(original.samples), .5, description)
        token = pymupdf.Pixmap(self.output / 'assets/page-13-ion-token.png')
        self.assertLess(token.height, (303.3 - 259) * 3 + 1)

    def test_small_html_figures_wrap_text_with_captions_below(self):
        for path in (self.root / 'docs').rglob('*.html'):
            html = path.read_text()
            for attributes, source in re.findall(r'<figure([^>]*)><img src="([^"]+)"', html):
                image = pymupdf.Pixmap(path.parent / source)
                self.assertEqual('figure-right' in attributes, max(image.width, image.height) < 155, source)
        for rule, caption in [('player-order', 'First Player Marker'),
                              ('position-marker', 'Position Marker'),
                              ('primary-weapon', 'Primary')]:
            html = (self.root / f'docs/glossary/glossary-{rule}.html').read_text()
            figure = html.index('<figure class="figure-right"')
            end = html.index('</figure>', figure)
            self.assertIn(caption, ''.join(HtmlContent(html[figure:end]).text))
            self.assertRegex(html[html.index('</h1>') + 5:figure], r'^\s*$')
            self.assertRegex(html[end + len('</figure>'):], r'^\s*<p>')
        css = (self.root / 'docs/style.css').read_text()
        self.assertIn('font-style: italic', css[css.index('figcaption {'):])

    def test_float_threshold_requires_both_dimensions_below_155(self):
        root = Path('/output/docs')
        block = Block('figure', page=17, figure=((0, 0, 10, 10), 'Marker', []))
        for size in [(154, 154), (155, 100), (100, 155), (154, 200)]:
            with self.subTest(size=size):
                html = render_blocks([block], {}, root / 'index.html', SOURCE, root, {},
                                     html=True, image_sizes={'page-17-marker.png': size})
                self.assertEqual('figure-right' in html, max(size) < 155)
                self.assertNotIn('<figcaption>', html)

    def test_left_sideslip_blue_arrow_survives_skipped_caption_clip_close(self):
        with pymupdf.open(SOURCE) as document:
            box = FIGURES[20][0][0]
            with isolate_figure(document, 20, FIGURE_GROUPS[20, 'A left sideslip'], box) as isolated:
                original = document[19].get_pixmap()
                artwork = isolated[0].get_pixmap()
                checked = 0
                for y in range(277, 304):
                    for x in range(494, 541):
                        if original.pixel(x, y) == (0, 174, 239):
                            self.assertEqual(artwork.pixel(x, y), original.pixel(x, y))
                            checked += 1
                self.assertGreater(checked, 30)

    def test_ion_image_immediately_follows_heading(self):
        self.assertTrue(self.rule('ion').startswith(
            '# ION\n\n![Ion token](../assets/page-13-ion-token.png)\n\n*Ion Token*\n\nA ship is'))

    def test_jam_image_immediately_follows_heading(self):
        self.assertTrue(self.rule('jam').startswith(
            '# JAM ([jam])\n\n![Jam token](../assets/page-14-jam-token.png)\n\n*Jam Token*\n\nPilots can jam'))

    def test_fuse_marker_image_follows_its_heading(self):
        image = '![Fuse marker](../assets/page-13-fuse-marker.png)'
        fuse = self.rule('fuse-marker')
        self.assertIn(image, fuse)
        self.assertLess(fuse.index('# FUSE MARKER'), fuse.index(image))
        self.assertLess(fuse.index(image), fuse.index('A device or obstacle'))
        self.assertNotIn(image, self.rule('fully-execute'))

    def test_victory_counters_stay_in_their_column(self):
        image = '![Victory counters](../assets/page-23-victory-counters.png)'
        victory = self.rule('victory-counters')
        self.assertIn(image, victory)
        self.assertLess(victory.index('# VICTORY COUNTERS'), victory.index(image))
        self.assertLess(victory.index(image), victory.index('Some scenarios'))
        self.assertNotIn(image, self.rule('tractor'))

    def test_unmapped_symbol_preserves_all_previous_files(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch.dict(SYMBOLS, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'Unmapped X-WingIcons'):
                convert(SOURCE, self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_html_files_links_assets_and_content(self):
        root = self.root / 'docs'
        pages = list(root.rglob('*.html'))
        self.assertEqual(len(pages), len(self.files))
        for page in pages:
            parsed = HtmlContent(page.read_text(encoding='utf-8'))
            self.assertIn(('div', {'class': 'page-content', 'tabindex': '0',
                                   'role': 'region', 'aria-label': 'Scrollable rules'}),
                          parsed.elements, page)
            self.assertEqual([attrs for tag, attrs in parsed.elements if tag == 'nav'],
                             [{'aria-label': 'Rules navigation'}], page)
            home = 'index.html' if page == root / 'index.html' else '../index.html'
            self.assertIn(('a', {'href': home}), parsed.elements, page)
            self.assertFalse(any(tag in {'pre', 'code'} for tag, _ in parsed.elements), page)
            text = ''.join(parsed.text)
            notice = '© & ™ Lucasfilm Ltd. The AMG logo is a ® of Atomic Mass Games.'
            self.assertEqual([tag for tag, _ in parsed.elements if tag == 'footer'], ['footer'], page)
            self.assertTrue(text.rstrip().endswith(notice), page)
            original = self.files[page.relative_to(root).with_suffix('.md').as_posix()]
            self.assertNotIn(notice, original, page)
            # HTML must preserve every paragraph, including symbols and emphasis text.
            for paragraph in original.split('\n\n'):
                if paragraph.startswith('<a ') or paragraph.startswith('!['):
                    continue
                paragraph = re.sub(r'^\s*(?:#+ |\d+\. |- )', '', plain_text(paragraph), flags=re.M)
                self.assertIn(re.sub(r'\s', '', paragraph), re.sub(r'\s', '', text), page)
            for tag, attrs in parsed.elements:
                url = attrs.get('href') or attrs.get('src')
                if not url:
                    continue
                path, _, anchor = unquote(url).partition('#')
                target = page.parent / path
                self.assertTrue(target.is_file(), f'{page}: {url}')
                if anchor and target.suffix == '.html':
                    self.assertIn(f'id="{anchor}"', target.read_text(encoding='utf-8'))
        css = (WEB / 'vendor/xwing-miniatures-font/xwing-miniatures.css').read_text()
        icons = HtmlContent(html_document(' '.join(SYMBOLS.values()), 'Symbols', root / 'index.html', root))
        self.assertEqual(len([t for t, _ in icons.elements if t == 'i']), len(SYMBOLS) - 2)
        for tag, attrs in icons.elements:
            if tag == 'i':
                self.assertIn('i.' + attrs['class'].split()[1] + ':before', css)
        self.assertIn('[hyperdrive]', ''.join(icons.text))
        attack = (root / 'glossary/glossary-attack.html').read_text()
        self.assertIn('<ol>', attack)
        self.assertIn('<ul>', attack)
        self.assertIn('<strong>Neutralize Results:</strong>', attack)
        self.assertIn('<p>The attack', attack)
        self.assertNotIn('.md', attack)
        self.assertTrue((root / 'vendor/xwing-miniatures-font/xwing-miniatures.ttf').is_file())

    def test_html_escapes_text_and_preserves_inline_styles(self):
        spans = [{'text': '<test> & ', 'font': 'EurostileLTStd-Cn', 'color': 0x004761},
                 {'text': 'bold', 'font': 'EurostileLTStd-Bold', 'color': 0x231F20}]
        text = inline_text(spans, {}, self.index, SOURCE, html=True)
        self.assertIn('<span style="color: #004761">&lt;test&gt; &amp;</span>', text)
        self.assertIn('<strong>bold</strong>', text)

    def test_html_subsection_target_is_on_heading_without_spacer_paragraph(self):
        text = '# Title\n\n<a id="section"></a>\n\n## Section\n\nBody'
        page = html_document(text, 'Title', self.index, self.index.parent)
        self.assertIn('<h2 id="section">Section</h2>', page)
        self.assertNotIn('<p><a id="section">', page)
        self.assertIn('<p>Body</p>', page)

    def test_pwa_bundle_covers_every_rule_and_uses_relative_urls(self):
        root = self.root / 'docs'
        manifest = json.loads((root / 'manifest.webmanifest').read_text())
        self.assertEqual(manifest['start_url'], './index.html')
        self.assertEqual(manifest['scope'], './')
        self.assertEqual(manifest['id'], './')
        self.assertEqual(manifest['display'], 'standalone')
        for icon in manifest['icons']:
            image = pymupdf.Pixmap(root / icon['src'])
            self.assertEqual(icon['sizes'], f'{image.width}x{image.height}')
            self.assertIn('maskable', icon['purpose'])
        touch = pymupdf.Pixmap(root / 'icons/apple-touch-icon.png')
        self.assertEqual((touch.width, touch.height), (180, 180))
        worker = (root / 'sw.js').read_text()
        self.assertNotIn('__VERSION__', worker)
        precache = json.loads(re.search(r'const PRECACHE = (.*);', worker)[1])
        expected = {p.relative_to(root).as_posix() for p in root.rglob('*')
                    if p.is_file() and p.suffix != '.pdf' and p.name != 'sw.js'}
        self.assertEqual(set(precache), expected)
        for page in root.rglob('*.html'):
            elements = HtmlContent(page.read_text(encoding='utf-8')).elements
            links = {attrs.get('rel'): attrs['href'] for tag, attrs in elements if tag == 'link'}
            self.assertEqual((page.parent / links['manifest']).resolve(),
                             (root / 'manifest.webmanifest').resolve())
            scripts = [attrs['src'] for tag, attrs in elements if tag == 'script']
            self.assertEqual(len(scripts), 1)
            self.assertEqual((page.parent / scripts[0]).resolve(), (root / 'pwa.js').resolve())

    def test_html_folder_is_portable_without_other_output_or_source_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'portable rules'
            shutil.copytree(self.root / 'docs', root)
            for page in root.rglob('*.html'):
                parsed = HtmlContent(page.read_text(encoding='utf-8'))
                for _, attrs in parsed.elements:
                    url = attrs.get('href') or attrs.get('src')
                    if not url:
                        continue
                    parsed_url = urlsplit(url)
                    self.assertFalse(parsed_url.scheme or parsed_url.netloc, url)
                    target = (page.parent / unquote(parsed_url.path)).resolve()
                    self.assertTrue(target.is_relative_to(root.resolve()), url)
                    self.assertTrue(target.is_file(), f'{page}: {url}')
                    if parsed_url.fragment and target.suffix == '.html':
                        self.assertIn(f'id="{parsed_url.fragment}"', target.read_text(encoding='utf-8'))
            for css in root.rglob('*.css'):
                for url in re.findall(r'url\(["\']?([^"\')]+)["\']?\)', css.read_text()):
                    target = (css.parent / unquote(url)).resolve()
                    self.assertTrue(target.is_relative_to(root.resolve()), url)
                    self.assertTrue(target.is_file(), f'{css}: {url}')
            self.assertEqual((root / SOURCE.name).read_bytes(), SOURCE.read_bytes())
            for original in (self.output / 'assets').glob('*.png'):
                self.assertEqual((root / 'assets' / original.name).read_bytes(), original.read_bytes())

    def test_markdown_section_folders_are_portable(self):
        self.assertEqual(self.index, self.output / 'index.md')
        self.assertEqual([p.name for p in self.output.glob('*.md')], ['index.md'])
        self.assertEqual(len(list((self.output / 'introduction').glob('*.md'))), 3)
        self.assertEqual(len(list((self.output / 'glossary').glob('*.md'))), 149)
        self.assertFalse((self.root / 'assets').exists())
        self.assertFalse((self.root / 'html').exists())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'portable markdown'
            shutil.copytree(self.output, root)
            self.assertEqual((root / SOURCE.name).read_bytes(), SOURCE.read_bytes())
            for page in root.rglob('*.md'):
                self.assertIn(page.parent, (root, root / 'introduction', root / 'glossary', root / 'appendix-examples'))
                for url in re.findall(r'\]\(([^)\n]+)\)', page.read_text(encoding='utf-8')):
                    parsed = urlsplit(url)
                    self.assertFalse(parsed.scheme or parsed.netloc, url)
                    target = (page.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(target.is_relative_to(root.resolve()), url)
                    self.assertTrue(target.is_file(), f'{page}: {url}')
                    if parsed.fragment and target.suffix == '.md':
                        self.assertIn(f'<a id="{parsed.fragment}"></a>', target.read_text(encoding='utf-8'))

    def test_html_page_frame_preserves_pdf_margins_without_body_text(self):
        root = self.root / 'docs'
        css = (root / 'style.css').read_text()
        for url in re.findall(r'url\("([^"]+)"\)', css):
            self.assertTrue((root / url).is_file(), f'Broken stylesheet asset: {url}')
        frame = pymupdf.Pixmap(root / 'assets/page-frame.png')
        self.assertEqual((frame.width, frame.height), (1836, 2376))
        with pymupdf.open(SOURCE) as document:
            original = document[2].get_pixmap(matrix=pymupdf.Matrix(3, 3))
        # Compare visible top and side margins against the original rendered PDF.
        for y in range(0, frame.height - 90, 12):
            for x in range(0, frame.width, 12):
                if y < 72 or x < 72 or x >= frame.width - 72:
                    self.assertEqual(frame.pixel(x, y), original.pixel(x, y), (x, y))
        # The interior must contain neither rule text nor page-number/copyright overlays.
        for y in range(120, frame.height - 90, 60):
            for x in range(120, frame.width - 120, 60):
                self.assertEqual(frame.pixel(x, y), (255, 255, 255), (x, y))

    def test_unresolved_reference_is_reported(self):
        spans = [{'text': 'missing rule', 'font': 'EurostileLTStd-Cn', 'color': 0x0F864C}]
        with self.assertRaisesRegex(ValueError, 'Cannot resolve rule reference'):
            inline_text(spans, {}, self.index, SOURCE)

    def test_missing_boundary_is_rejected(self):
        with pymupdf.open(SOURCE) as original, pymupdf.open() as short:
            short.insert_pdf(original, from_page=0, to_page=1)
            with self.assertRaisesRegex(ValueError, 'Missing conversion boundary'):
                extract_blocks(short)


if __name__ == '__main__':
    unittest.main()
