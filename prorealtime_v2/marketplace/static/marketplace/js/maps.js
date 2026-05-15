document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.spot.available').forEach((spot) => {
    spot.addEventListener('mouseenter', () => spot.closest('.map-shell')?.classList.add('selecting'));
    spot.addEventListener('mouseleave', () => spot.closest('.map-shell')?.classList.remove('selecting'));
  });

  const map = document.querySelector('[data-drag-map]');
  if (!map) return;
  let draggedSpot = null;
  const updateFormCoordinates = (spot, x, y) => {
    const row = document.querySelector(`[data-form-spot-id="${spot.dataset.spotId}"]`);
    if (!row) return;
    const inputs = row.querySelectorAll('input');
    const xInput = Array.from(inputs).find((input) => input.name.endsWith('-x'));
    const yInput = Array.from(inputs).find((input) => input.name.endsWith('-y'));
    if (xInput) xInput.value = x.toFixed(2);
    if (yInput) yInput.value = y.toFixed(2);
  };
  map.querySelectorAll('.draggable-spot').forEach((spot) => {
    spot.addEventListener('dragstart', (event) => {
      draggedSpot = spot;
      event.dataTransfer.effectAllowed = 'move';
    });
  });
  map.addEventListener('dragover', (event) => event.preventDefault());
  map.addEventListener('drop', (event) => {
    event.preventDefault();
    if (!draggedSpot) return;
    const rect = map.getBoundingClientRect();
    const x = Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100));
    const y = Math.max(0, Math.min(100, ((event.clientY - rect.top) / rect.height) * 100));
    draggedSpot.style.left = `${x}%`;
    draggedSpot.style.top = `${y}%`;
    updateFormCoordinates(draggedSpot, x, y);
    draggedSpot = null;
  });
});
