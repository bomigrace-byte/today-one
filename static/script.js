const drawButton = document.getElementById("draw-button");
const doneButton = document.getElementById("done-button");
const backButton = document.getElementById("back-button");
const saveButton = document.getElementById("save-button");
const recordBackButton = document.getElementById("record-back-button");
const homeButton = document.getElementById("home-button");

const homeScreen = document.getElementById("home-screen");
const missionScreen = document.getElementById("mission-screen");
const recordScreen = document.getElementById("record-screen");
const completeScreen = document.getElementById("complete-screen");

const category = document.getElementById("category");
const missionTitle = document.getElementById("mission-title");
const missionDescription = document.getElementById("mission-description");

const discoveryInput = document.getElementById("discovery-input");
const photoInput = document.getElementById("photo-input");
const photoPreview = document.getElementById("photo-preview");
const savedDiscovery = document.getElementById("saved-discovery");

const emotionButtons = document.querySelectorAll(".emotion-button");

let currentAction = null;
let selectedEmotion = "";


drawButton.addEventListener("click", async () => {

    const response = await fetch("/api/today");
    const action = await response.json();

    currentAction = action;

    category.textContent = action.category;
    missionTitle.textContent = action.title;
    missionDescription.textContent = action.description;

    homeScreen.classList.add("hidden");
    missionScreen.classList.remove("hidden");
});


doneButton.addEventListener("click", () => {

    missionScreen.classList.add("hidden");
    recordScreen.classList.remove("hidden");

});


backButton.addEventListener("click", () => {

    missionScreen.classList.add("hidden");
    homeScreen.classList.remove("hidden");

});


photoInput.addEventListener("change", () => {

    const file = photoInput.files[0];

    if (file) {
        const imageUrl = URL.createObjectURL(file);

        photoPreview.src = imageUrl;
        photoPreview.classList.remove("hidden");
    }

});


emotionButtons.forEach((button) => {

    button.addEventListener("click", () => {

        emotionButtons.forEach((item) => {
            item.classList.remove("selected");
        });

        button.classList.add("selected");

        selectedEmotion = button.dataset.emotion;
    });

});


saveButton.addEventListener("click", async () => {

    const discovery = discoveryInput.value.trim();

    if (!discovery) {
        alert("발견한 내용을 한 줄이라도 적어주세요.");
        return;
    }

    const formData = new FormData();

    formData.append("action_id", currentAction.id);
    formData.append("content", discovery);
    formData.append("emotion", selectedEmotion);

    if (photoInput.files[0]) {
        formData.append("image", photoInput.files[0]);
    }

    const response = await fetch("/api/discoveries", {
        method: "POST",
        body: formData
    });

    const result = await response.json();

    if (!response.ok) {
        alert(result.error);
        return;
    }

    savedDiscovery.textContent = discovery;

    recordScreen.classList.add("hidden");
    completeScreen.classList.remove("hidden");

});


recordBackButton.addEventListener("click", () => {

    recordScreen.classList.add("hidden");
    missionScreen.classList.remove("hidden");

});


homeButton.addEventListener("click", () => {

    discoveryInput.value = "";
    photoInput.value = "";
    photoPreview.src = "";
    photoPreview.classList.add("hidden");

    selectedEmotion = "";

    emotionButtons.forEach((button) => {
        button.classList.remove("selected");
    });

    completeScreen.classList.add("hidden");
    homeScreen.classList.remove("hidden");

});