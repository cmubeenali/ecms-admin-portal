function toggleNotification(notification) {
    const details = notification.querySelector('.notification-details');
    if (details.style.display === 'none') {
      details.style.display = 'block';
    } else {
      details.style.display = 'none';
    }
  }
  