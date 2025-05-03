//redirect functions
function home() {
    window.location.href = "index.html";
}

function about() {
    window.location.href = "about.html";
}

function shop() {
    window.location.href = "shop.html";
}
// Preloader animation
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(() => {
        document.querySelector(".preloader").style.animation = "fadeOut 1s ease-out forwards";

        setTimeout(() => {
            document.querySelector(".preloader").style.display = "none";
            document.querySelector(".main-content").style.display = "block";
        }, 1000);
    }, 2500);
});

// Intersection Observer setup
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('show');
        }
    });
}, { threshold: 0.1 });


//scroll animation
document.querySelectorAll('.scroll-animation').forEach(element => {
    observer.observe(element);
});

