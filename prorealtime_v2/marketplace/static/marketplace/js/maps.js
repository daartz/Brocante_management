document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.spot.available').forEach((spot) => {
    spot.addEventListener('mouseenter', () => spot.closest('.map-shell')?.classList.add('selecting'));
    spot.addEventListener('mouseleave', () => spot.closest('.map-shell')?.classList.remove('selecting'));
  });
});
