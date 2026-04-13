const footer = `
<footer class="site-footer">
        
        <div class="abstract-lines"></div>
        
        <div class="footer-content">
            
            <div class="company-info">
                <div class="logo">
                    <span class="logo-icon"><i class="">⧲</i></span>
                    Dine<span style="color: var(--ternary-color);">Sphere</span>
                </div>
                <p>
                    Connecting food enthusiasts with the city's finest dining spots. Simple reservations, real reviews, and exclusive experiences.
                </p>

                <div class="social-icons">
                    <a href="#" aria-label="X"><i class="fab fa-twitter"></i></a>
                    <a href="#" aria-label="LinkedIn"><i class="fab fa-linkedin-in"></i></a>
                    <a href="#" aria-label="Instagram"><i class="fab fa-instagram"></i></a>
                    <a href="#" aria-label="Facebook"><i class="fab fa-facebook-f"></i></a>
                </div>

                <a href="#top" class="back-to-top">
                    <i class="fas fa-chevron-up"></i> BACK TO TOP
                </a>
            </div>

            <div>
                <h3 class="footer-col-title">Site Map</h3>
                <ul class="footer-link-list">
                    <li><a href="/">Home</a></li>
                    <li><a href="/#who">About Us</a></li>
                    <li><a href="/uh/business-register/">Join as Partner</a></li>
                    <li><a href="/uh/auth?mode=signup">Create Account</a></li>
                    <li><a href="/profile">My Profile</a></li>
                </ul>
            </div>

            <div>
                <h3 class="footer-col-title">Legal</h3>
                <ul class="footer-link-list">
                    <li><a href="#">Privacy Policy</a></li>
                    <li><a href="#">Terms of Services</a></li>
                    <li><a href="#">Lawyer's Corners</a></li>
                </ul>
            </div>
        </div>

     
    </footer>
`;

document.body.insertAdjacentHTML('beforeend', footer);