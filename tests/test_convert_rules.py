from pathlib import Path
from html.parser import HTMLParser
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import pymupdf

from convert_rules import (
    SOURCE, SYMBOLS, TEXT_FLAGS, FIGURES, STOP_SECTION,
    convert, extract_blocks, inline_text, translated, html_document, WEB,
)


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
        self.assertEqual(re.findall(r'^## .+$', index, re.M), ['## Introduction', '## Glossary'])
        self.assertIn('The glossary lists all gameplay terms and phases in detail.', index)
        self.assertIn('This reference is the definitive source', index)
        self.assertLess(index.index('## Introduction'), index.index('introduction-golden-rules.md'))
        self.assertLess(index.index('## Glossary'), index.index('glossary-abilities.md'))
        links = re.findall(r'\]\(([^)]+\.md)\)', index)
        self.assertEqual(len(links), 152)
        self.assertEqual(set(links), set(self.files) - {'index.md'})
        self.assertEqual(sum(p.startswith('introduction/') for p in links), 3)
        self.assertEqual(sum(p.startswith('glossary/') for p in links), 149)
        for link in links:
            folder, filename = link.split('/')
            self.assertRegex(filename, '^' + folder + r'-[a-z0-9]+(?:-[a-z0-9]+)*\.md$')
            self.assertEqual(len(re.findall(r'^# ', self.files[link], re.M)), 1)

    def test_boundary_skips_cover_and_all_appendices(self):
        self.assertNotIn(STOP_SECTION, self.text)
        self.assertNotIn('EXTENDED EXAMPLES', self.text)
        self.assertNotIn('Ability Queue Example #1', self.text)
        self.assertNotIn('Lucasfilm', self.text)
        with pymupdf.open(SOURCE) as document:
            blocks = extract_blocks(document)
        self.assertEqual(min(b.page for b in blocks), 2)
        self.assertEqual(max(b.page for b in blocks), 23)
        self.assertEqual([b.text for b in blocks if b.kind == 'section'], ['INTRODUCTION', 'GLOSSARY'])

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
        self.assertEqual(links, 626)
        self.assertRegex(self.rule('ability-queue'), r'Rules%20Reference%20v1\.4\.6-1\.pdf#page=24')
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
        self.assertEqual((image.width, image.height), (792, 351))
        abilities = self.rule('abilities')
        self.assertLess(abilities.index('## Pilot and Ship Abilities'), abilities.index('![Pilot and ship abilities]'))
        self.assertLess(abilities.index('![Pilot and ship abilities]'), abilities.index('## Replacement Effects'))
        self.assertNotIn('After you perform an action', abilities)
        with pymupdf.open(SOURCE) as document:
            box = FIGURES[21][0][0]
            original = document[20].get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=pymupdf.Rect(box))
            crop = pymupdf.Pixmap(self.output / 'assets/page-21-bank-compared-with-sideslip.png')
            self.assertEqual(original.samples, crop.samples, 'Crop masks must not erase illustration content')

    def test_ion_image_immediately_follows_heading(self):
        self.assertTrue(self.rule('ion').startswith(
            '# ION\n\n![Ion token](../assets/page-13-ion-token.png)\n\nA ship is'))

    def test_jam_image_immediately_follows_heading(self):
        self.assertTrue(self.rule('jam').startswith(
            '# JAM ([jam])\n\n![Jam token](../assets/page-14-jam-token.png)\n\nPilots can jam'))

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
            self.assertFalse(any(tag in {'pre', 'code'} for tag, _ in parsed.elements), page)
            text = ''.join(parsed.text)
            original = self.files[page.relative_to(root).with_suffix('.md').as_posix()]
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
                self.assertIn(page.parent, (root, root / 'introduction', root / 'glossary'))
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
