if ('serviceWorker' in navigator && ['https:', 'http:'].includes(location.protocol)) {
  const worker = new URL('sw.js', document.currentScript.src);
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(worker).catch(error => {
      console.warn('Offline rules could not be enabled:', error);
    });
  });
}
