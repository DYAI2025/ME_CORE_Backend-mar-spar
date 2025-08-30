(async () => {
  const dock = await InputDock.attach({
    api: 'https://b0bfe21bd-8080.preview.abacusai.app',
    target: '#dock',
    ui: true
  });
  dock.on(ev => console.log('InputDock', ev));
})();