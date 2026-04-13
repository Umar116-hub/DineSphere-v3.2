function updateFavouritesUI() { 

    const items = document.querySelectorAll('.modern-card');
    items.forEach(item => {
        const isFav = item.getAttribute('data-isfav');
        const favBtn = item.querySelector('.fav-btn');
        console.log(isFav);
        
        if (isFav) {
            favBtn.classList.add('active');
        } else {
            favBtn.classList.remove('active');
        }
    });
}
function toggleFavorite(event, restaurantId) {
    event.stopPropagation();
    if (!IS_AUTHENTICATED) {
        showNotification('Please login to add to favourites!');
        return;
    }
    updateFavouritesUI()
    const btn = event.currentTarget;
    const icon = btn.querySelector('i');
    const card = btn.closest('.modern-card');
    const restaurantName = card.getAttribute('data-name');
    
    // Get CSRF token from cookie
    const csrftoken = getCookie('csrftoken');
    
    // Make AJAX request to toggle favorite
    fetch('/toggle-favourite/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: new URLSearchParams({
            'restaurant_id': restaurantId,
        })
    })
    .then(response => {
        if (response.status === 302 || response.redirected) {
            // Redirected to login
            window.location.href = '/uh/auth/';
            return null;
        }
        return response.json();
    })
    .then(data => {
        if (data === null) return;
        
        if (data.success) {
            if (data.favourited) {
                // Changed to favorite
                icon.classList.replace('fa-regular', 'fa-solid');
                btn.classList.add('active');
                showNotification(`${restaurantName} added to favorites!`);
                
                // Refresh the page or update the favorites carousel
                location.reload();
            } else {
                // Removed from favorite
                icon.classList.replace('fa-solid', 'fa-regular');
                btn.classList.remove('active');
                showNotification(`${restaurantName} removed from favorites!`);
                
                // Refresh the page to update favorites carousel
                location.reload();
            }
        } else {
            alert('Error updating favorite: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating favorite');
    });
}


// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show simple notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #4CAF50;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 1000;
        font-size: 14px;
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}
document.addEventListener('DOMContentLoaded', () => {
    // The "Inspect Element" Simulator
window.addEventListener('load', () => {
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
    }, 300); 
});
    const initCarousels = () => {
        const carousels = document.querySelectorAll('.carousel');
        
        carousels.forEach((carousel, i) => {
            const track = carousel.querySelector('.carousel-track');
            const cards = carousel.querySelectorAll('.modern-card');
            const prevBtn = carousel.querySelector('.btn-left');
            const nextBtn = carousel.querySelector('.btn-right');
            
            if (!track || cards.length === 0) return;

            let index = 0;
            const gap = 20; // Must match CSS gap

            const getVisibleCount = () => {
                const w = window.innerWidth;
                if (w <= 480) return 1;
                if (w <= 768) return 2;
                if (w <= 1024) return 3;
                return 5;
            };

            const updateCarousel = () => {
    // 1. Get current widths
    const containerWidth = track.parentElement.offsetWidth;
    const cardWidth = cards[0].offsetWidth;
    const gap = 20;

    // 2. Calculate how many cards are fully/mostly visible
    // We use floor to ensure we don't get stuck if a card is 1% visible
    const visibleCards = Math.floor(containerWidth / (cardWidth + gap));
    
    // 3. Fix: maxIndex should allow you to reach the very last item
    // If visibleCards is 1 (mobile), maxIndex is cards.length - 1
    const maxIndex = cards.length - Math.max(1, visibleCards);
    
    // 4. Boundary check
    if (index > maxIndex) index = maxIndex;
    if (index < 0) index = 0;

    // 5. Move the track
    const moveX = index * (cardWidth + gap);
    track.style.transform = `translateX(-${moveX}px)`;
    
    // 6. Fix Button Visibility
    if (prevBtn) {
        prevBtn.style.visibility = index === 0 ? 'hidden' : 'visible';
    }
    if (nextBtn) {
        // Only hide if we are at the absolute limit
        nextBtn.style.visibility = index >= maxIndex ? 'hidden' : 'visible';
    }
};

            nextBtn?.addEventListener('click', () => {
                index++;
                updateCarousel();
            });

            prevBtn?.addEventListener('click', () => {
                index--;
                updateCarousel();
            });

            // Touch support for mobile swipe
            let startX, moveX;
            track.addEventListener('touchstart', e => startX = e.touches[0].clientX);
            track.addEventListener('touchmove', e => moveX = e.touches[0].clientX);
            track.addEventListener('touchend', () => {
                if (startX - moveX > 50) index++; // swipe left
                if (startX - moveX < -50) index--; // swipe right
                updateCarousel();
            });

            window.addEventListener('resize', updateCarousel);
            // Wait for images to load or small delay to get correct offsetWidth
            setTimeout(updateCarousel, 100);
        });
    };

    const mainPage = document.getElementById('main-page');
    if (mainPage) {
        // Force recalculation of layout
        setTimeout(() => {
            mainPage.style.height = 'auto'; // Reset height
            mainPage.style.height = `${mainPage.scrollHeight}px`; // Force recalculation
        }, 100);
    }
 

    initCarousels();
    // syncFavoritesUI();
});


