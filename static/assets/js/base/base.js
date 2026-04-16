document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const btnToggle = document.getElementById('btn-toggle') || document.querySelector('.mobile-menu-btn');
    const overlay = document.getElementById('overlay');
    const submenuBtns = document.querySelectorAll('.submenu-btn');
    const modal = document.getElementById('myModal');
    const openModalBtn = document.getElementById('openModalBtn');
    const closeModalBtn = document.querySelector('.close-modal');
    const userProfile = document.querySelector('.user-profile');

    // Toggle Sidebar
    if (btnToggle) {
        btnToggle.addEventListener('click', () => {
            if (window.innerWidth > 768) {
                sidebar.classList.toggle('collapsed');
            } else {
                sidebar.classList.toggle('mobile-open');
                if (overlay) overlay.classList.toggle('active');
            }
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
        });
    }

    // Submenu Logic
    submenuBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const parent = this.parentElement;

            document.querySelectorAll('.nav-item.has-submenu').forEach(item => {
                if (item !== parent) {
                    item.classList.remove('open');
                }
            });

            parent.classList.toggle('open');
            
            if (sidebar.classList.contains('collapsed')) {
                sidebar.classList.remove('collapsed');
            }
        });
    });

    // User Profile Dropdown
    if (userProfile) {
        userProfile.addEventListener('click', (e) => {
            e.stopPropagation();
            userProfile.classList.toggle('open');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!userProfile.contains(e.target)) {
                userProfile.classList.remove('open');
            }
        });
    }

    // Modal functionality
    if (openModalBtn && modal) {
        openModalBtn.addEventListener('click', () => {
            modal.style.display = 'block';
        });
    }

    if (closeModalBtn && modal) {
        closeModalBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    if (modal) {
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('mobile-open');
            if (overlay) overlay.classList.remove('active');
        }
    });
}); 