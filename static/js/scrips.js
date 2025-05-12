// Menu handlers
function setupMenus() {
    const walletMenuBtn = document.getElementById('walletMenuBtn');
    const walletPopup = document.getElementById('walletPopup');
    const menuToggle = document.getElementById('menuToggle');
    const extendedMenu = document.getElementById('extendedMenu');

    if (walletMenuBtn && walletPopup) {
        walletMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            walletPopup.style.display = walletPopup.style.display === 'none' ? 'block' : 'none';
        });
    }

    if (menuToggle && extendedMenu) {
        menuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            extendedMenu.style.display = extendedMenu.style.display === 'none' ? 'block' : 'none';
        });
    }

    document.addEventListener('click', () => {
        if (walletPopup) walletPopup.style.display = 'none';
        if (extendedMenu) extendedMenu.style.display = 'none';
    });
}

document.addEventListener("DOMContentLoaded", function () {
    setupMenus();
    const quizForm = document.getElementById("quiz-form");

    if (quizForm) {
        quizForm.addEventListener("submit", function (event) {
            event.preventDefault();
            let correctAnswers = 0;
            let totalQuestions = 0;

            const questions = document.querySelectorAll(".question");
            questions.forEach((question, index) => {
                totalQuestions++;
                const selectedAnswer = document.querySelector(`input[name="q${index}"]:checked`);
                if (selectedAnswer && selectedAnswer.value === "correct") {
                    correctAnswers++;
                }
            });

            alert(`You scored ${correctAnswers} out of ${totalQuestions}`);
        });
    }
});


document.addEventListener("DOMContentLoaded", function () {
    // Rotating Web3 & Blockchain Definitions
    const definitions = [
        "Web3 is the decentralized internet, powered by blockchain technology.",
        "Blockchain is a secure and transparent digital ledger for recording transactions.",
        "Smart contracts are self-executing contracts with coded terms on the blockchain."
    ];

    let index = 0;
    function updateIntroText() {
        document.getElementById("intro-text").innerText = definitions[index];
        index = (index + 1) % definitions.length;
    }

    setInterval(updateIntroText, 5000); // Change text every 5 seconds
    updateIntroText(); // Initial call
});

function fetchRoadmap(careerId) {
    fetch(`/generate_roadmap/${careerId}`)
    .then(response => response.json())
    .then(data => {
        document.getElementById("roadmap-text").innerText = data.roadmap;
    })
    .catch(error => {
        console.error("Error fetching roadmap:", error);
    });
}