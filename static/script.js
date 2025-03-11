document.addEventListener('DOMContentLoaded', () => {
    // Show login/upload/instructions box with animation
    const boxes = document.querySelectorAll('.login-box, .upload-box, .instructions-box');
    boxes.forEach(box => {
        box.classList.add('show');
    });

    // Animate results when they appear
    const results = document.querySelector('.results');
    if (results) {
        setTimeout(() => {
            results.classList.add('show');
        }, 300);
    }

    // Animate instruction steps sequentially
    const steps = document.querySelectorAll('.instruction-step');
    steps.forEach((step, index) => {
        setTimeout(() => {
            step.classList.add('show');
        }, index * 500);
    });

    // Function to animate hospital list
    function animateHospitalList() {
        const hospitalList = document.querySelector('.instruction-step ul');
        if (hospitalList) {
            setTimeout(() => {
                hospitalList.classList.add('show');
            }, 200); // Delay to sync with content fade-in
        }

        // Optional: Staggered animation for each hospital item (uncomment to enable)
        /*
        const hospitalItems = document.querySelectorAll('.instruction-step ul li');
        hospitalItems.forEach((item, index) => {
            setTimeout(() => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(20px)';
                item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, 10);
            }, index * 200); // 200ms delay between each item
        });
        */
    }

    // Call on initial load for hospitals page
    animateHospitalList();

    // Add loading animation on form submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const btn = form.querySelector('.btn');
            const originalText = btn.innerHTML; // Store the original button text
            btn.innerHTML = 'Processing...';
            btn.disabled = true;

            if (form.action.includes('/hospitals')) {
                e.preventDefault(); // Prevent default form submission
                const formData = new FormData(form);
                const hospitalContent = document.getElementById('hospital-content');
                const loadingDiv = document.getElementById('loading') || document.createElement('div');

                // Ensure loading div is set up
                if (!loadingDiv.id) {
                    loadingDiv.id = 'loading';
                    loadingDiv.style.textAlign = 'center';
                    loadingDiv.innerHTML = '<p>Loading hospitals...</p>';
                    hospitalContent.before(loadingDiv);
                }
                loadingDiv.style.display = 'block';
                hospitalContent.style.opacity = '0'; // Fade out current content

                fetch(form.action, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.text())
                .then(html => {
                    // Replace entire document (simulating Flask's render)
                    document.open();
                    document.write(html);
                    document.close();

                    // Re-apply animations after content loads
                    setTimeout(() => {
                        const newHospitalContent = document.getElementById('hospital-content');
                        const newLoadingDiv = document.getElementById('loading');
                        newLoadingDiv.style.display = 'none';
                        newHospitalContent.style.opacity = '0'; // Start hidden
                        newHospitalContent.style.display = 'block';
                        setTimeout(() => {
                            newHospitalContent.style.transition = 'opacity 0.5s ease';
                            newHospitalContent.style.opacity = '1'; // Fade in
                            animateHospitalList(); // Animate hospital list
                        }, 100); // Small delay for DOM settling
                    }, 100);

                    btn.innerHTML = originalText;
                    btn.disabled = false;
                })
                .catch(error => {
                    console.error('Error:', error);
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    loadingDiv.style.display = 'none';
                    hospitalContent.style.opacity = '1';
                });
            } else {
                // For other forms (e.g., upload page)
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }, 2000);
            }
        });
    });

    // Update file info when files are selected
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.querySelector('.file-info');
    if (fileInput && fileInfo) {
        fileInput.addEventListener('change', () => {
            fileInfo.textContent = `Selected: ${fileInput.files.length} files`;
        });
    }

    // Toggle dark mode with persistence
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const body = document.body;
    if (darkModeToggle) {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            body.setAttribute('data-theme', 'dark');
            darkModeToggle.querySelector('.toggle-icon').textContent = '☀️';
        } else {
            darkModeToggle.querySelector('.toggle-icon').textContent = '🌓';
        }

        darkModeToggle.addEventListener('click', () => {
            if (body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                darkModeToggle.querySelector('.toggle-icon').textContent = '🌓';
                localStorage.setItem('theme', 'light');
            } else {
                body.setAttribute('data-theme', 'dark');
                darkModeToggle.querySelector('.toggle-icon').textContent = '☀️';
                localStorage.setItem('theme', 'dark');
            }
        });
    }

    // Hamburger menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navbarLinks = document.querySelector('.navbar-links');
    if (hamburger && navbarLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navbarLinks.classList.toggle('active');
        });

        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navbarLinks.classList.remove('active');
            });
        });
    }

    // Smooth scroll for any anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add active class to nav links based on current page
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath || (currentPath === '/' && link.getAttribute('href') === '/login')) {
            link.classList.add('active');
        }
    });

    // Navigate to hospitals page directly
    const viewHospitalsBtn = document.getElementById('view-hospitals-btn');
    if (viewHospitalsBtn) {
        viewHospitalsBtn.addEventListener('click', () => {
            window.location.href = '/hospitals';
        });
    }
});