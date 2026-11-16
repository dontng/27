/* Same fit-to-width principle as m2; long political options may wrap in one column. */
(() => {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  function fitOptions() {
    if (!context) return;
    for (const group of document.querySelectorAll('.options')) {
      const items = [...group.children];
      const style = getComputedStyle(items[0]);
      context.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
      // Printing uses the A4 content width, independent of a narrow phone viewport.
      const width = matchMedia('print').matches
        ? 176 * 96 / 25.4 - parseFloat(getComputedStyle(group).marginLeft)
        : group.clientWidth;
      const gap = parseFloat(getComputedStyle(group).columnGap) || 0;
      const required = Math.max(...items.map(item => context.measureText(item.textContent).width)) + 6;
      const columns = [4, 2, 1].find(n => n === 1 || required <= (width - (n - 1) * gap) / n);
      group.style.gridTemplateColumns = `repeat(${columns}, minmax(0, 1fr))`;
    }
  }
  let frame;
  const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(fitOptions); };
  document.fonts.ready.then(() => { fitOptions(); document.body.dataset.ready = 'true'; });
  new ResizeObserver(schedule).observe(document.querySelector('main'));
  window.addEventListener('beforeprint', fitOptions);
  window.addEventListener('afterprint', schedule);
})();
