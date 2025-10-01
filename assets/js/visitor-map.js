(function () {
  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  function formatCount(count) {
    if (typeof count !== 'number') {
      return 'Visitor';
    }
    if (count === 1) {
      return '1 visitor';
    }
    return count + ' visitors';
  }

  function showMessage(container, message) {
    container.innerHTML = '';
    const note = document.createElement('p');
    note.className = 'visitor-map__message';
    note.textContent = message;
    container.appendChild(note);
  }

  function renderMap(container, data) {
    container.innerHTML = '';

    const map = L.map(container, {
      scrollWheelZoom: false,
      worldCopyJump: true,
    }).setView([20, 0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 6,
    }).addTo(map);

    if (!Array.isArray(data) || data.length === 0) {
      showMessage(container, 'Add visitor data to display the map.');
      return;
    }

    const bounds = [];

    data.forEach(function (entry) {
      const lat = Number(entry.latitude);
      const lon = Number(entry.longitude);

      if (Number.isNaN(lat) || Number.isNaN(lon)) {
        return;
      }

      const count = Number(entry.count);
      const radius = Number.isNaN(count)
        ? 6
        : Math.max(6, Math.min(20, Math.sqrt(Math.max(count, 1)) * 3));

      const marker = L.circleMarker([lat, lon], {
        radius: radius,
        color: '#006d77',
        weight: 1,
        fillColor: '#83c5be',
        fillOpacity: 0.8,
      }).addTo(map);

      const title = entry.name || 'Visitor';
      marker.bindPopup('<strong>' + title + '</strong><br />' + formatCount(count));

      bounds.push([lat, lon]);
    });

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [24, 24], maxZoom: 4 });
    }
  }

  function init() {
    if (typeof L === 'undefined') {
      return;
    }

    const container = document.querySelector('[data-visitor-map]');
    if (!container) {
      return;
    }

    const dataSrc = container.getAttribute('data-src');
    if (!dataSrc) {
      showMessage(container, 'Visitor data source is missing.');
      return;
    }

    fetch(dataSrc)
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Request failed with status ' + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        renderMap(container, data);
      })
      .catch(function (error) {
        console.error('Visitor map error:', error);
        showMessage(container, 'Unable to load visitor data right now.');
      });
  }

  ready(init);
})();
