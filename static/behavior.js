let keyTimes = [];
let lastKeyTime = 0;

function captureKey(e) {
    let now = performance.now();

    if (lastKeyTime > 0) {
        keyTimes.push(now - lastKeyTime);
    }
    lastKeyTime = now;
}

function calcSpeed() {
    let input = document.getElementById("behaviorInput") || document.getElementById("regInput");

    if (input.value.length > 1) {
        let duration = keyTimes.reduce((a, b) => a + b, 0);
        window.typingSpeed = input.value.length / (duration / 1000);
        window.averageDelay = duration / keyTimes.length;
    }
}

function registerBehavior() {
    fetch("/save-behavior", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            typed_text: document.getElementById("regInput").value,
            typing_speed: window.typingSpeed || 0,
            average_delay: window.averageDelay || 0
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("result").innerHTML = data.message;
    });
}

function verifyBehavior() {
    fetch("/verify-behavior", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            typed_text: document.getElementById("behaviorInput").value,
            typing_speed: window.typingSpeed || 0,
            average_delay: window.averageDelay || 0
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("result").innerHTML = data.message;
    });
}
