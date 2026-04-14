document.addEventListener('DOMContentLoaded', () => {
    const drawerForm = document.getElementById('drawerForm');
    const clearBtn = document.getElementById('clearForm');

    // --- CLEAR FORM ---
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            drawerForm.reset();
        });
    }

    // --- SEARCH FILTER ---
    const searchInput = document.getElementById('staffSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.clickable-card');
            cards.forEach(card => {
                const name = (card.querySelector('.user-display-name')?.textContent || '').toLowerCase();
                const email = (card.querySelector('.user-contact')?.textContent || '').toLowerCase();
                if (name.includes(query) || email.includes(query)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // --- DELETE LOGIC (Selection Mode) ---
    const deleteBtn = document.querySelector('.btn-delete');
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const selectedCard = document.querySelector('.clickable-card.selected');
            
            if (!selectedCard) {
                return alert("Please select a staff member to remove.");
            }

            const staffId = selectedCard.dataset.id;
            const staffName = selectedCard.querySelector('.user-display-name')?.textContent || "this user";

            const modal = document.getElementById('confirmModal');
            const modalOverlay = document.getElementById('modalOverlay');
            
            document.getElementById('modalMessage').innerText = `Revoke access for ${staffName.trim()}?`;
            
            modal.classList.add('show');
            modalOverlay.classList.add('show');

            window.pendingDeleteUrl = `/uh/remove-staff/${staffId}/`;
        });
    }
});
