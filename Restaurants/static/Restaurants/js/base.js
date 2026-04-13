// Page Loader Handling
window.addEventListener('load', () => {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.classList.add('fade-out');
        setTimeout(() => {
            loader.style.display = 'none';
        }, 400); // Match CSS transition
    }
});

// Show loader on refresh/navigation
window.addEventListener('beforeunload', () => {
    const loader = document.getElementById('page-loader');
    if (loader && !window.location.protocol.startsWith('mailto')) {
        loader.style.display = 'flex';
        loader.classList.remove('fade-out');
    }
});

// Select all nav items
  const navItems = document.querySelectorAll('.nav-links .nav-item');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      // Remove 'active' class from all items
      navItems.forEach(nav => nav.classList.remove('active'));
      // Add 'active' class to the clicked item
      item.classList.add('active');
    });
  });

// Drop Down Menu
document.addEventListener('DOMContentLoaded', function() {
    const trigger = document.getElementById('business-trigger');
    const list = document.getElementById('business-list');
    const nameDisplay = document.getElementById('current-business-name');
    try {
            trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        list.classList.toggle('show');
    });

    // We use Event Delegation because list items will be added/removed dynamically
    list.addEventListener('click', function(e) {
        const item = e.target.closest('.dropdown-item');
        if (!item) return;

        // 1. Capture Old Data (The one currently in the header)
        const oldId = nameDisplay.getAttribute('data-current-id');
        const oldName = nameDisplay.innerText;

        // 2. Capture New Data (The one you just clicked)
        const newId = item.getAttribute('data-id');
        const newName = item.innerText;

        // 3. Perform the SWAP in the UI
        // Update Header
        nameDisplay.innerText = newName;
        nameDisplay.setAttribute('data-current-id', newId);

        // Update List: Remove the new one, Add back the old one
        item.remove();
        const newListItem = document.createElement('li');
        newListItem.className = 'dropdown-item';
        newListItem.setAttribute('data-id', oldId);
        newListItem.innerText = oldName;
        list.appendChild(newListItem);

        list.classList.remove('show');

        // 4. Fire AJAX
        sendBusinessUpdate(newId);
    });

    document.addEventListener('click', () => list.classList.remove('show'));

    function sendBusinessUpdate(id) {
        const csrftoken = getCookie('csrftoken');
        fetch('/business/switch/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({ 'business_id': id })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // If your backend handles the full page data update, 
                // you might want to reload here:
                window.location.reload(); 
                console.log("Switched!");
            }
        });
    }

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
        
    } catch (error) {
        console.log("MOYE MOYE");
        
    }


    const logoutBtn = document.getElementById('dashboard-logout');
    const modal = document.getElementById('confirmModal');
    const modalOverlay = document.getElementById('modalOverlay');
    const modalConfirm = document.getElementById('modalConfirm');
    const modalMessage = document.getElementById('modalMessage');
    const modalTitle = modal.querySelector('h3');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            // 1. Update Modal Content for Logout
            modalTitle.innerText = "Leaving so soon?";
            modalMessage.innerText = "Are you sure you want to log out of your dashboard?";
            modalConfirm.innerText = "Logout";
            modalConfirm.style.backgroundColor = "var(--primary-color)"; // Match your teal theme

            // 2. Set the global pending action to the logout URL
            window.pendingActionUrl = "/uh/logout/";
            
            // 3. Show Modal
            modal.classList.add('show');
            modalOverlay.classList.add('show');
        });
    }

    // --- Modular Confirm Handler ---
    // This handles Logout, Deletions, or Toggles based on whatever is in window.pendingActionUrl
    modalConfirm?.addEventListener('click', () => {
        if (!window.pendingActionUrl) return;

        const actionForm = document.createElement('form');
        actionForm.method = 'POST';
        actionForm.action = window.pendingActionUrl;
        
        const csrf = document.createElement('input');
        csrf.type = 'hidden';
        csrf.name = 'csrfmiddlewaretoken';
        // Get CSRF from the hidden input in your existing forms or cookie
        csrf.value = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
        
        actionForm.appendChild(csrf);
        document.body.appendChild(actionForm);
        actionForm.submit();
    });

    // --- Close Modal Logic ---
    const closeModal = () => {
        modal.classList.remove('show');
        modalOverlay.classList.remove('show');
        // Reset button state for next use (e.g. if a delete happens later)
        modalConfirm.classList.add('btn-danger');
        modalConfirm.innerText = "Delete";
    };

    document.getElementById('modalCancel')?.addEventListener('click', closeModal);
    modalOverlay?.addEventListener('click', closeModal);

    // Helper for CSRF if not present in DOM
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
});

/**
 * Universal AJAX Update Function
 * @param {string} modelName - 'tables', 'business', or 'holidays'
 * @param {number} id - The instance ID
 * @param {Object} data - Key-value pairs of form data
 */
async function triggerUpdate(modelName, id, data) {
    const url = `/business/${modelName}/update/${id}/`;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.status === 'success') {
            // Booyah! Reload to see changes or update UI manually
            window.location.reload();
        } else {
            alert("Error updating record");
        }
    } catch (error) {
        console.error("Update failed:", error);
    }
}

// Example usage when clicking your "Save Changes" button in the drawer:
/*
const formData = {
    name: document.querySelector('[name="table_name"]').value,
    capacity: document.querySelector('[name="capacity"]').value
};
triggerUpdate('tables', selectedId, formData);
*/

document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.clickable-card');
    const deselectBtn = document.getElementById('deselectBtn');
    const deleteBtn = document.getElementById('deleteBtn');
    const selectedCountText = document.getElementById('selectedCount');
    const actionPanel = document.getElementById('actionPanel');
    const actionButtons = document.querySelector('.action-buttons');

    // Count visible buttons excluding the Deselect button to check for "Permanent" buttons
    const permanentButtons = actionButtons.querySelectorAll('.panel-btn:not(#deselectBtn)').length;

    const syncUI = () => {
        const selectedCards = document.querySelectorAll('.clickable-card.selected');
        const count = selectedCards.length;
        
        selectedCountText.innerText = count;

        if (count > 0) {
            // 1. Enable Buttons
            deselectBtn.disabled = false;
            if (deleteBtn) deleteBtn.disabled = false;
            
            // 2. Show panel if it's in "Floating" mode (No permanent buttons)
            if (permanentButtons === 0) {
                actionPanel.classList.add('show');
            }
        } else {
            // 1. Disable Buttons
            deselectBtn.disabled = true;
            if (deleteBtn) deleteBtn.disabled = true;
            
            // 2. Hide panel if it's in "Floating" mode
            if (permanentButtons === 0) {
                actionPanel.classList.remove('show');
            }
        }
    };

    // Card Click Logic
    cards.forEach(card => {
        card.addEventListener('click', () => {
            const isAlreadySelected = card.classList.contains('selected');
            cards.forEach(c => c.classList.remove('selected'));
            if (!isAlreadySelected) card.classList.add('selected');
            syncUI();
        });
    });

    // Deselect Logic
    deselectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        cards.forEach(c => c.classList.remove('selected'));
        syncUI();
    });

    // Handle initial state: If permanent buttons exist, keep it shown
    if (permanentButtons > 0) {
        actionPanel.classList.add('show');
    }
    syncUI(); 
});

document.addEventListener('DOMContentLoaded', () => {
    const dynamicHeader = document.getElementById('header-dynamic');
    if (dynamicHeader) {
        // Force switch to the new dynamic tab on page load
        switchTab('dynamic', dynamicHeader);
    }
});

function switchTab(tabName, element) {
    // 1. Reset all tab headers
    document.querySelectorAll('.table-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 2. Activate current tab header
    element.classList.add('active');

    // 3. Hide ALL content sections in the stack
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });

    // 4. Show the specific content for this tab
    const targetContent = document.getElementById('tab-' + tabName);
    if (targetContent) {
        targetContent.style.display = 'block';
    }
}

function closeDynamicTab(event) {
    event.stopPropagation();

    window.location.href = "/business/"
    
    // Remove the elements from DOM
    const header = document.getElementById('header-dynamic');
    const content = document.getElementById('tab-dynamic');
    
    if (header) header.remove();
    if (content) content.remove();

    // Revert to Logs
    switchTab('logs', document.getElementById('header-logs'));
    
    // Clean URL so refresh doesn't bring it back
    window.history.replaceState({}, document.title, window.location.pathname);

}