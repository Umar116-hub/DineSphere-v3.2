// 1. Create the Registry of Page-Specific Mappers
const PageMappers = {
    // Logic for Table Page
   tables: (form, data) => {
    form.action = `/business/tables/update/${data.id}/`;
    form.querySelector('[name="name"]').value = data.name;
    form.querySelector('[name="base_price"]').value = data.price;
    form.querySelector('[name="table_size"]').value = data.size;
    form.querySelector('[name="seating_type"]').value = data.seating;
    form.querySelector('[name="is_combinable"]').checked = data.combinable === "true";
    form.querySelector('[name="is_available"]').checked = data.available === "true";
},
    // Logic for Staff Page
    staff: (form, data) => {
        form.action = `/business/staff/update/${data.id}/`;
        if(form.querySelector('[name="full_name"]')) form.querySelector('[name="full_name"]').value = data.name;
    },

    // Logic for Holidays
    holidays: (form, data) => {
        form.action = `/business/holidays/update/${data.id}/`;
        
        form.querySelector('[name="date"]').value = data.date;
        form.querySelector('[name="name"]').value = data.name;
        form.querySelector('[name="closed_full_day"]').checked = data.closed_full_day === "True";
        form.querySelector('[name="adjusted_opening_hour"]').value = data.adjusted_opening_hour ?? 'None';
        form.querySelector('[name="adjusted_closing_hour"]').value = data.adjusted_closing_hour ?? 'None';


    },
    // Logic for Business Info
    business: (form, data) => {
    // 1️⃣ Update form action URL
    form.action = `/business/business-info/update/${data.id}/`;
    // 2️⃣ Direct text inputs
    const fields = [
        'name', 
        'title', 
        'address', 
        'phone_number', 
        'about_restaurant', 
        'fb_link', 
        'website_link', 
        'city'
    ];

    fields.forEach(field => {
        const input = form.querySelector(`[name="${field}"]`);
        if (input && data[field] !== undefined) input.value = data[field];
    });

    // 3️⃣ Boolean / checkbox fields
    const boolFields = [
        'has_top_offers'
    ];
    boolFields.forEach(field => {
        const checkbox = form.querySelector(`[name="${field}"]`);
        if (checkbox && data[field] !== undefined) {
            checkbox.checked = data[field] === "true" || data[field] === true;
        }
    });

    // 4️⃣ Numeric / integer fields
    const numericFields = [
        'default_opening_hour',
        'default_closing_hour',
        'slot_duration_minutes',
        'allow_advance_booking_days',
        'cool_down'
    ];
    numericFields.forEach(field => {
    const input = form.querySelector(`[name="${field}"]`);
    if (input && data[field] !== undefined) {
        // If it's a time input, format it so the browser can display it
        if (input.type === 'time') {
            input.value = formatTimeTo24h(data[field]);
        } else {
            input.value = data[field];
        }
    }
});

    // 5️⃣ Array / multiple selections (e.g., seating types)
   // Handle seating types (checkbox group)
    // 1️⃣ Select all checkboxes with name="seating_types"
const seatingCheckboxes = document.querySelectorAll('#id_seating_types input[name="seating_types"]');

// 2️⃣ Get the comma-separated data from your clicked card
// Example: data-seating_types="1,2,3"
const card = document.querySelector('.clickable-card.selected'); // assuming you have a selected card
if (card && seatingCheckboxes.length > 0) {
    const selectedValues = card.dataset.seating_types.split(',').map(v => v.trim());

    seatingCheckboxes.forEach(checkbox => {
        checkbox.checked = selectedValues.includes(checkbox.value);
    });
}
    },
    reviews: (form, data) => {},


};

document.addEventListener('DOMContentLoaded', function() {
    let selectedId = null;
    let selectedData = {};
    
    // Determine which page we are on
    const currentModel = document.querySelector('.which-model').dataset.model.trim();
    
    const form = document.getElementById('drawerForm');

    // --- OPEN DRAWER (Add button) ---
    const addBtn = document.querySelector('.btn-add');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const sideDrawer = document.getElementById('sideDrawer');
    const closeDrawer = document.getElementById('closeDrawer');

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            selectedId = null;         // clear selection
            selectedData = {};         // clear data
            form.reset();              // clear the form
            form.action = window.location.href;
            drawerOverlay.classList.add('show');
            sideDrawer.classList.add('open');
        });
    }

    // --- CLOSE DRAWER (cross button and overlay click) ---
    if (closeDrawer) {
        closeDrawer.addEventListener('click', () => {
            drawerOverlay.classList.remove('show');
            sideDrawer.classList.remove('open');
        });
    }

    // Optional: clicking outside the drawer closes it
    if (drawerOverlay) {
        drawerOverlay.addEventListener('click', () => {
            drawerOverlay.classList.remove('show');
            sideDrawer.classList.remove('open');
        });
    }

    // --- SELECTION ---
    document.querySelectorAll('.clickable-card').forEach(card => {

        
        card.addEventListener('click', function() {
            document.querySelectorAll('.clickable-card').forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
            selectedId = this.dataset.id;
            selectedData = { ...this.dataset };
        });
    });
    

    // --- UNIVERSAL UPDATE ---
    const updateBtn = document.querySelector('.btn-update');
    if (updateBtn) {
        updateBtn.addEventListener('click', () => {
            if (!selectedId) return alert("Please select an item first!");

            // 1. Find the mapping function for the current page
            const mapper = PageMappers[currentModel];
            
            if (mapper) {
                // 2. Open UI
                document.getElementById('drawerOverlay').classList.add('show');
                document.getElementById('sideDrawer').classList.add('open');

                // 3. Let the mapper fill the form
                mapper(form, selectedData);
            } else {
                console.error(`No mapper defined for model: ${currentModel}`);
            }
        });
    }

    // --- UNIVERSAL DELETE ---
    const deleteBtn = document.querySelector('.btn-delete');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            if (!selectedId) return alert("Please select an item first!");
            
            // Set the generic modal action
            const modal = document.getElementById('confirmModal');
            document.getElementById('modalMessage').innerText = `Delete ${selectedData}?`;
            modal.classList.add('show');
            document.getElementById('modalOverlay').classList.add('show');

            // Setup the specific delete URL
            
            window.pendingDeleteUrl = window.location.origin + window.location.pathname + `delete/${selectedId}/`;
        });
        
    }// --- REFRESH BUTTON ---
    const refreshBtn = document.querySelector('.btn-view');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            location.reload(); // simple page reload
        });
    }

    // --- DELETE MODAL CLOSE BUTTON ---
    const modalOverlay = document.getElementById('modalOverlay');
    const modalClose = document.getElementById('modalCancel'); // add this button in HTML
    const confirmModal = document.getElementById('confirmModal');
        modalClose?.addEventListener('click', () => {
        confirmModal.classList.remove('show');
        modalOverlay.classList.remove('show');
    });
/**
 * Converts "6:01 p.m." or "18:01" to "18:01" (24-hour format)
 */
function formatTimeTo24h(timeStr) {
    if (!timeStr) return null;
    
    // If it's already in 24h format (e.g. "18:01"), just return it
    if (/^\d{2}:\d{2}/.test(timeStr)) return timeStr.substring(0, 5);

    const [time, modifier] = timeStr.split(' ');
    let [hours, minutes] = time.split(':');

    if (hours === '12') hours = '00';
    
    // Clean up minutes (remove dots from p.m. / a.m.)
    const cleanModifier = modifier.toLowerCase().replace(/\./g, '');

    if (cleanModifier === 'pm') {
        hours = parseInt(hours, 10) + 12;
    }

    return `${hours.toString().padStart(2, '0')}:${minutes.padStart(2, '0')}`;
}

// --- Inside your form submit listener ---
form.addEventListener('submit', async (e) => {
    // PREVENT DOUBLE CLICKS: Disable submit button globally
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    }

    if (form.action.includes('/update/')) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // 1. Convert Time Fields (Fixes the ValidationError)
        const timeFields = [
            'default_opening_hour', 
            'default_closing_hour', 
            'adjusted_opening_hour', 
            'adjusted_closing_hour'
        ];
        
        timeFields.forEach(field => {
            if (data[field]) {
                data[field] = formatTimeTo24h(data[field]);
            }
        });

        // 2. Many-to-Many logic...
        const seatingTypes = [];
        form.querySelectorAll('input[name="seating_types"]:checked').forEach(cb => {
            seatingTypes.push(cb.value);
        });
        if (seatingTypes.length > 0) data['seating_types'] = seatingTypes;

        // 3. Boolean logic...
        form.querySelectorAll('input[type="checkbox"]:not([name="seating_types"])').forEach(cb => {
            data[cb.name] = cb.checked;
        });

        // Send Fetch request...
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.status === 'success') location.reload();
        else {
            alert("Update failed!");
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Changes';
            }
        }
    }
    // If it's NOT an /update/ action (e.g. adding a table), it simply proceeds 
    // with the normal HTML form POST, but the button is safely disabled!
});
});

// Modular Modal Confirm (Stays the same for every page)
document.getElementById('modalConfirm')?.addEventListener('click', () => {
    const deleteForm = document.createElement('form');
    deleteForm.method = 'POST';
    deleteForm.action = window.pendingDeleteUrl;
    
    const csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrfmiddlewaretoken';
    csrf.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    deleteForm.appendChild(csrf);
    document.body.appendChild(deleteForm);
    deleteForm.submit();
});

