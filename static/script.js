const drawButton = document.getElementById("draw-button");
const doneButton = document.getElementById("done-button");
const backButton = document.getElementById("back-button");
const saveButton = document.getElementById("save-button");
const recordBackButton = document.getElementById("record-back-button");
const homeButton = document.getElementById("home-button");
const historyButton = document.getElementById("history-button");
const historyBackButton = document.getElementById("history-back-button");

const deleteDiscoveryButton =
    document.getElementById("delete-discovery-button");


const homeScreen = document.getElementById("home-screen");
const missionScreen = document.getElementById("mission-screen");
const recordScreen = document.getElementById("record-screen");
const completeScreen = document.getElementById("complete-screen");
const reflectionScreen = document.getElementById("reflection-screen");
const historyScreen = document.getElementById("history-screen");
const historyList = document.getElementById("history-list");

const detailScreen = document.getElementById("detail-screen");
const detailBackButton =
    document.getElementById("detail-back-button");

const detailDate =
    document.getElementById("detail-date");

const detailCategory =
    document.getElementById("detail-category");

const detailActionTitle =
    document.getElementById("detail-action-title");

const detailActionDescription =
    document.getElementById("detail-action-description");

const detailContent =
    document.getElementById("detail-content");

const detailImage =
    document.getElementById("detail-image");

const detailEmotion =
    document.getElementById("detail-emotion");

const detailQuestion =
    document.getElementById("detail-question");

const detailReflection =
    document.getElementById("detail-reflection");

const detailPrevious =
    document.getElementById("detail-previous");

const previousDiscoveryButton =
    document.getElementById("previous-discovery-button");

const detailPreviousContent =
    document.getElementById("detail-previous-content");


const category =
    document.getElementById("category");

const missionTitle =
    document.getElementById("mission-title");

const missionDescription =
    document.getElementById("mission-description");

const chainMessage =
    document.getElementById("chain-message");


const discoveryInput =
    document.getElementById("discovery-input");

const photoInput =
    document.getElementById("photo-input");

const photoPreview =
    document.getElementById("photo-preview");

const savedDiscovery =
    document.getElementById("saved-discovery");

const aiQuestion =
    document.getElementById("ai-question");

const reflectionInput =
    document.getElementById("reflection-input");

const reflectionSaveButton =
    document.getElementById("reflection-save-button");

const reflectionSkipButton =
    document.getElementById("reflection-skip-button");


const emotionButtons =
    document.querySelectorAll(".emotion-button");


let currentAction = null;
let selectedEmotion = "";
let currentDiscoveryId = null;


// =========================================================
// 감정에 맞는 질문
// =========================================================

function getEmotionQuestion(emotion) {

    if (!emotion) {
        return "";
    }

    if (emotion.includes("좋았다")) {
        return "그때 기분은 어땠나요?";
    }

    return "그때 어떤 느낌이었나요?";
}


// =========================================================
// 기록 화면 초기화
// =========================================================

function resetRecordForm() {

    discoveryInput.value = "";
    photoInput.value = "";

    photoPreview.src = "";
    photoPreview.classList.add("hidden");

    reflectionInput.value = "";

    savedDiscovery.textContent = "";
    aiQuestion.textContent = "";

    selectedEmotion = "";
    currentDiscoveryId = null;


    emotionButtons.forEach((button) => {
        button.classList.remove("selected");
    });
}


// =========================================================
// 오늘의 행동 뽑기
// =========================================================

drawButton.addEventListener("click", async () => {

    try {

        drawButton.disabled = true;
        drawButton.textContent = "하나 고르는 중...";


        const response =
            await fetch("/api/today");


        if (!response.ok) {

            throw new Error(
                `오늘의 행동 요청 실패: ${response.status}`
            );

        }


        const action =
            await response.json();


        currentAction = action;


        category.textContent =
            action.category || "";

        missionTitle.textContent =
            action.title || "";

        missionDescription.textContent =
            action.description || "";


        if (action.personalized) {

            chainMessage.textContent =
                action.chain_message ||
                "지난 발견에서 이어진 행동이에요.";

            chainMessage.classList.remove(
                "hidden"
            );

        } else {

            chainMessage.textContent = "";

            chainMessage.classList.add(
                "hidden"
            );

        }


        homeScreen.classList.add(
            "hidden"
        );

        missionScreen.classList.remove(
            "hidden"
        );


    } catch (error) {

        console.error(
            "오늘의 행동을 가져오지 못했습니다:",
            error
        );


        alert(
            "오늘의 행동을 가져오지 못했어요. 잠시 후 다시 시도해주세요."
        );


    } finally {

        drawButton.disabled = false;
        drawButton.textContent = "✦ 하나 뽑기";

    }

});


// =========================================================
// 행동 완료 → 새로운 기록 시작
// =========================================================

doneButton.addEventListener("click", () => {

    resetRecordForm();

    missionScreen.classList.add(
        "hidden"
    );

    recordScreen.classList.remove(
        "hidden"
    );

});


// =========================================================
// 미션 화면에서 돌아가기
// =========================================================

backButton.addEventListener("click", () => {

    missionScreen.classList.add(
        "hidden"
    );

    homeScreen.classList.remove(
        "hidden"
    );

});


// =========================================================
// 사진 선택
// =========================================================

photoInput.addEventListener("change", () => {

    const file =
        photoInput.files[0];


    if (file) {

        const imageUrl =
            URL.createObjectURL(file);


        photoPreview.src =
            imageUrl;

        photoPreview.classList.remove(
            "hidden"
        );

    }

});


// =========================================================
// 감정 선택
// =========================================================

emotionButtons.forEach((button) => {

    button.addEventListener(
        "click",
        () => {

            emotionButtons.forEach(
                (item) => {

                    item.classList.remove(
                        "selected"
                    );

                }
            );


            button.classList.add(
                "selected"
            );


            selectedEmotion =
                button.dataset.emotion;

        }
    );

});


// =========================================================
// 발견 기록 저장
// =========================================================

saveButton.addEventListener(
    "click",
    async () => {

        const discovery =
            discoveryInput.value.trim();


        if (!discovery) {

            alert(
                "발견한 내용을 한 줄이라도 적어주세요."
            );

            return;

        }


        if (!currentAction) {

            alert(
                "오늘의 행동 정보를 찾을 수 없어요."
            );

            return;

        }


        try {

            saveButton.disabled = true;
            saveButton.textContent =
                "저장하는 중...";


            const formData =
                new FormData();


            const actionId =
                Number.isInteger(
                    currentAction.id
                )
                    ? currentAction.id
                    : "";


            formData.append(
                "action_id",
                actionId
            );


            formData.append(
                "action_title",
                currentAction.title || ""
            );


            formData.append(
                "action_description",
                currentAction.description || ""
            );


            formData.append(
                "action_category",
                currentAction.category || ""
            );


            formData.append(
                "content",
                discovery
            );


            formData.append(
                "emotion",
                selectedEmotion
            );


            formData.append(
                "previous_discovery_id",
                currentAction.previous_discovery_id ?? ""
            );


            if (photoInput.files[0]) {

                formData.append(
                    "image",
                    photoInput.files[0]
                );

            }


            const response =
                await fetch(
                    "/api/discoveries",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.error ||
                    "발견 저장에 실패했습니다."
                );

            }


            currentDiscoveryId =
                result.id;


            savedDiscovery.textContent =
                discovery;


            // 방금 생성된 기록에 대한 AI 질문
            const aiResponse =
                await fetch(
                    "/api/ai/question",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            discovery_id:
                                currentDiscoveryId,

                            discovery:
                                discovery
                        })
                    }
                );


            const aiResult =
                await aiResponse.json();


            if (!aiResponse.ok) {

                throw new Error(
                    aiResult.error ||
                    "AI 질문 생성에 실패했습니다."
                );

            }


            aiQuestion.textContent =
                aiResult.question || "";


            recordScreen.classList.add(
                "hidden"
            );

            reflectionScreen.classList.remove(
                "hidden"
            );


        } catch (error) {

            console.error(
                "발견 저장 또는 AI 질문 생성 실패:",
                error
            );


            alert(
                error.message
            );


        } finally {

            saveButton.disabled = false;
            saveButton.textContent =
                "기록하기";

        }

    }
);


// =========================================================
// 기록 화면에서 돌아가기
// =========================================================

recordBackButton.addEventListener(
    "click",
    () => {

        recordScreen.classList.add(
            "hidden"
        );

        missionScreen.classList.remove(
            "hidden"
        );

    }
);


// =========================================================
// 처음으로
// =========================================================

homeButton.addEventListener(
    "click",
    () => {

        resetRecordForm();

        currentAction = null;


        completeScreen.classList.add(
            "hidden"
        );

        homeScreen.classList.remove(
            "hidden"
        );

    }
);


// =========================================================
// 지난 발견 보기
// =========================================================

historyButton.addEventListener(
    "click",
    async () => {

        try {

            const response =
                await fetch(
                    "/api/discoveries"
                );


            if (!response.ok) {

                throw new Error(
                    "지난 발견을 불러오지 못했습니다."
                );

            }


            const discoveries =
                await response.json();


            historyList.innerHTML = "";


            if (discoveries.length === 0) {

                historyList.textContent =
                    "아직 기록한 발견이 없어요.";

            } else {

                discoveries.forEach(
                    (discovery) => {

                        const card =
                            document.createElement(
                                "div"
                            );


                        card.classList.add(
                            "history-card"
                        );


                        card.addEventListener(
                            "click",
                            () => {

                                showDiscoveryDetail(
                                    discovery.id
                                );

                            }
                        );


                        // 날짜
                        const date =
                            document.createElement(
                                "p"
                            );

                        date.classList.add(
                            "history-date"
                        );

                        date.textContent =
                            discovery.date;

                        card.appendChild(
                            date
                        );


                        // 실제로 했던 행동
                        const action =
                            document.createElement(
                                "p"
                            );

                        action.classList.add(
                            "history-action"
                        );

                        action.textContent =
                            discovery.action_title ||
                            "오늘의 행동";

                        card.appendChild(
                            action
                        );


                        // 발견 질문
                        const discoveryQuestion =
                            document.createElement(
                                "p"
                            );

                        discoveryQuestion.classList.add(
                            "history-discovery-label"
                        );

                        discoveryQuestion.textContent =
                            "무엇이 있었나요?";

                        card.appendChild(
                            discoveryQuestion
                        );


                        // 내가 발견한 것
                        const content =
                            document.createElement(
                                "p"
                            );

                        content.classList.add(
                            "history-content"
                        );

                        content.textContent =
                            discovery.content;

                        card.appendChild(
                            content
                        );


                        // 연쇄 사건
                        if (
                            discovery.previous_discovery
                        ) {

                            const chain =
                                document.createElement(
                                    "div"
                                );

                            chain.classList.add(
                                "history-chain"
                            );


                            const chainText =
                                document.createElement(
                                    "p"
                                );

                            chainText.classList.add(
                                "history-chain-text"
                            );

                            chainText.textContent =
                                "↳ 이전 발견에서 이어졌어요";


                            chain.appendChild(
                                chainText
                            );

                            card.appendChild(
                                chain
                            );

                        }


                        // AI 질문
                        if (
                            discovery.ai_question
                        ) {

                            const questionLabel =
                                document.createElement(
                                    "p"
                                );

                            questionLabel.classList.add(
                                "history-ai-label"
                            );

                            questionLabel.textContent =
                                "AI의 질문";


                            const question =
                                document.createElement(
                                    "p"
                                );

                            question.classList.add(
                                "history-question"
                            );

                            question.textContent =
                                discovery.ai_question;


                            card.appendChild(
                                questionLabel
                            );

                            card.appendChild(
                                question
                            );

                        }


                        // 나의 생각
                        if (
                            discovery.reflection
                        ) {

                            const reflectionLabel =
                                document.createElement(
                                    "p"
                                );

                            reflectionLabel.classList.add(
                                "history-reflection-label"
                            );

                            reflectionLabel.textContent =
                                "나의 생각";


                            const reflection =
                                document.createElement(
                                    "p"
                                );

                            reflection.classList.add(
                                "history-reflection"
                            );

                            reflection.textContent =
                                discovery.reflection;


                            card.appendChild(
                                reflectionLabel
                            );

                            card.appendChild(
                                reflection
                            );

                        }


                        // 감정
                        if (
                            discovery.emotion
                        ) {

                            const emotionQuestion =
                                document.createElement(
                                    "p"
                                );

                            emotionQuestion.classList.add(
                                "history-emotion-label"
                            );

                            emotionQuestion.textContent =
                                getEmotionQuestion(
                                    discovery.emotion
                                );


                            card.appendChild(
                                emotionQuestion
                            );


                            const emotion =
                                document.createElement(
                                    "p"
                                );

                            emotion.classList.add(
                                "history-emotion"
                            );

                            emotion.textContent =
                                discovery.emotion;


                            card.appendChild(
                                emotion
                            );

                        }


                        // 사진
                        if (
                            discovery.image_path
                        ) {

                            const image =
                                document.createElement(
                                    "img"
                                );

                            image.src =
                                discovery.image_path;

                            image.classList.add(
                                "history-image"
                            );

                            image.alt =
                                "발견 기록 사진";


                            card.appendChild(
                                image
                            );

                        }


                        historyList.appendChild(
                            card
                        );

                    }
                );

            }


            homeScreen.classList.add(
                "hidden"
            );

            historyScreen.classList.remove(
                "hidden"
            );


        } catch (error) {

            console.error(
                "지난 발견 불러오기 실패:",
                error
            );


            alert(
                "지난 발견을 불러오지 못했어요."
            );

        }

    }
);


// =========================================================
// 지난 발견에서 처음으로
// =========================================================

historyBackButton.addEventListener(
    "click",
    () => {

        historyScreen.classList.add(
            "hidden"
        );

        homeScreen.classList.remove(
            "hidden"
        );

    }
);


// =========================================================
// 생각 저장
// =========================================================

reflectionSaveButton.addEventListener(
    "click",
    async () => {

        const reflection =
            reflectionInput.value.trim();


        if (!reflection) {

            alert(
                "생각을 한 줄이라도 적어주세요."
            );

            return;

        }


        if (!currentDiscoveryId) {

            alert(
                "기록 정보를 찾을 수 없어요."
            );

            return;

        }


        try {

            reflectionSaveButton.disabled =
                true;

            reflectionSaveButton.textContent =
                "저장하는 중...";


            const response =
                await fetch(
                    `/api/discoveries/${currentDiscoveryId}/reflection`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            reflection:
                                reflection
                        })
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.error ||
                    "생각 저장에 실패했습니다."
                );

            }


            reflectionInput.value = "";


            reflectionScreen.classList.add(
                "hidden"
            );

            completeScreen.classList.remove(
                "hidden"
            );


        } catch (error) {

            console.error(
                "생각 저장 실패:",
                error
            );


            alert(
                error.message
            );


        } finally {

            reflectionSaveButton.disabled =
                false;

            reflectionSaveButton.textContent =
                "답변 저장";

        }

    }
);


// =========================================================
// AI 질문 건너뛰기
// =========================================================

reflectionSkipButton.addEventListener(
    "click",
    () => {

        reflectionInput.value = "";


        reflectionScreen.classList.add(
            "hidden"
        );

        completeScreen.classList.remove(
            "hidden"
        );

    }
);


// =========================================================
// 발견 상세 보기
// =========================================================

async function showDiscoveryDetail(
    discoveryId
) {

    try {

        const response =
            await fetch(
                `/api/discoveries/${discoveryId}`
            );


        const discovery =
            await response.json();


        if (!response.ok) {

            throw new Error(
                discovery.error ||
                "발견 상세 정보를 불러오지 못했습니다."
            );

        }


        // ★ 삭제에 사용할 현재 기록 ID
        currentDiscoveryId =
            discovery.id;


        detailDate.textContent =
            discovery.date;


        detailCategory.textContent =
            discovery.category;


        detailActionTitle.textContent =
            discovery.action_title;


        detailActionDescription.textContent =
            discovery.action_description;


        detailContent.textContent =
            discovery.content;


        // 이전 발견
        if (
            discovery.previous_discovery
        ) {

            detailPrevious.classList.remove(
                "hidden"
            );


            detailPreviousContent.textContent =
                discovery.previous_discovery.content;


            previousDiscoveryButton.onclick =
                () => {

                    showDiscoveryDetail(
                        discovery.previous_discovery.id
                    );

                };


        } else {

            detailPrevious.classList.add(
                "hidden"
            );


            detailPreviousContent.textContent =
                "";


            previousDiscoveryButton.onclick =
                null;

        }


        // 사진
        if (
            discovery.image_path
        ) {

            detailImage.src =
                discovery.image_path;


            detailImage.classList.remove(
                "hidden"
            );


        } else {

            detailImage.src = "";


            detailImage.classList.add(
                "hidden"
            );

        }


        // 감정
        detailEmotion.textContent =
            discovery.emotion || "";


        // AI 질문
        detailQuestion.textContent =
            discovery.ai_question ||
            "아직 AI 질문이 없습니다.";


        // 나의 생각
        detailReflection.textContent =
            discovery.reflection ||
            "아직 남긴 생각이 없습니다.";


        historyScreen.classList.add(
            "hidden"
        );


        detailScreen.classList.remove(
            "hidden"
        );


    } catch (error) {

        console.error(
            "발견 상세 보기 실패:",
            error
        );


        alert(
            error.message
        );

    }

}


// =========================================================
// 발견 상세에서 지난 발견으로 돌아가기
// =========================================================

detailBackButton.addEventListener(
    "click",
    () => {

        detailScreen.classList.add(
            "hidden"
        );

        historyScreen.classList.remove(
            "hidden"
        );

    }
);


// =========================================================
// 기록 삭제
// =========================================================

deleteDiscoveryButton.addEventListener(
    "click",
    async () => {

        if (!currentDiscoveryId) {

            alert(
                "삭제할 기록을 찾을 수 없어요."
            );

            return;

        }


        const confirmed =
            confirm(
                "이 기록을 삭제할까요?\n\n" +
                "삭제한 기록은 다시 복구할 수 없습니다."
            );


        if (!confirmed) {

            return;

        }


        try {

            deleteDiscoveryButton.disabled =
                true;

            deleteDiscoveryButton.textContent =
                "삭제하는 중...";


            const response =
                await fetch(
                    `/api/discoveries/${currentDiscoveryId}`,
                    {
                        method: "DELETE"
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.error ||
                    "기록 삭제에 실패했습니다."
                );

            }


            currentDiscoveryId = null;


            detailScreen.classList.add(
                "hidden"
            );

            historyScreen.classList.remove(
                "hidden"
            );


            // 목록 다시 불러오기
            await loadHistory();


        } catch (error) {

            console.error(
                "기록 삭제 실패:",
                error
            );


            alert(
                error.message
            );


        } finally {

            deleteDiscoveryButton.disabled =
                false;

            deleteDiscoveryButton.textContent =
                "기록 삭제";

        }

    }
);


// =========================================================
// 지난 발견 목록을 다시 불러오는 함수
// =========================================================

async function loadHistory() {

    const response =
        await fetch(
            "/api/discoveries"
        );


    if (!response.ok) {

        throw new Error(
            "지난 발견을 불러오지 못했습니다."
        );

    }


    const discoveries =
        await response.json();


    historyList.innerHTML = "";


    if (discoveries.length === 0) {

        historyList.textContent =
            "아직 기록한 발견이 없어요.";

        return;

    }


    discoveries.forEach(
        (discovery) => {

            const card =
                document.createElement(
                    "div"
                );


            card.classList.add(
                "history-card"
            );


            card.addEventListener(
                "click",
                () => {

                    showDiscoveryDetail(
                        discovery.id
                    );

                }
            );


            const date =
                document.createElement(
                    "p"
                );

            date.classList.add(
                "history-date"
            );

            date.textContent =
                discovery.date;

            card.appendChild(
                date
            );


            const action =
                document.createElement(
                    "p"
                );

            action.classList.add(
                "history-action"
            );

            action.textContent =
                discovery.action_title ||
                "오늘의 행동";

            card.appendChild(
                action
            );


            const discoveryQuestion =
                document.createElement(
                    "p"
                );

            discoveryQuestion.classList.add(
                "history-discovery-label"
            );

            discoveryQuestion.textContent =
                "무엇이 있었나요?";

            card.appendChild(
                discoveryQuestion
            );


            const content =
                document.createElement(
                    "p"
                );

            content.classList.add(
                "history-content"
            );

            content.textContent =
                discovery.content;

            card.appendChild(
                content
            );


            if (
                discovery.previous_discovery
            ) {

                const chain =
                    document.createElement(
                        "div"
                    );

                chain.classList.add(
                    "history-chain"
                );


                const chainText =
                    document.createElement(
                        "p"
                    );

                chainText.classList.add(
                    "history-chain-text"
                );

                chainText.textContent =
                    "↳ 이전 발견에서 이어졌어요";


                chain.appendChild(
                    chainText
                );

                card.appendChild(
                    chain
                );

            }


            if (
                discovery.ai_question
            ) {

                const questionLabel =
                    document.createElement(
                        "p"
                    );

                questionLabel.classList.add(
                    "history-ai-label"
                );

                questionLabel.textContent =
                    "AI의 질문";


                const question =
                    document.createElement(
                        "p"
                    );

                question.classList.add(
                    "history-question"
                );

                question.textContent =
                    discovery.ai_question;


                card.appendChild(
                    questionLabel
                );

                card.appendChild(
                    question
                );

            }


            if (
                discovery.reflection
            ) {

                const reflectionLabel =
                    document.createElement(
                        "p"
                    );

                reflectionLabel.classList.add(
                    "history-reflection-label"
                );

                reflectionLabel.textContent =
                    "나의 생각";


                const reflection =
                    document.createElement(
                        "p"
                    );

                reflection.classList.add(
                    "history-reflection"
                );

                reflection.textContent =
                    discovery.reflection;


                card.appendChild(
                    reflectionLabel
                );

                card.appendChild(
                    reflection
                );

            }


            if (
                discovery.emotion
            ) {

                const emotionQuestion =
                    document.createElement(
                        "p"
                    );

                emotionQuestion.classList.add(
                    "history-emotion-label"
                );

                emotionQuestion.textContent =
                    getEmotionQuestion(
                        discovery.emotion
                    );


                card.appendChild(
                    emotionQuestion
                );


                const emotion =
                    document.createElement(
                        "p"
                    );

                emotion.classList.add(
                    "history-emotion"
                );

                emotion.textContent =
                    discovery.emotion;


                card.appendChild(
                    emotion
                );

            }


            if (
                discovery.image_path
            ) {

                const image =
                    document.createElement(
                        "img"
                    );

                image.src =
                    discovery.image_path;

                image.classList.add(
                    "history-image"
                );

                image.alt =
                    "발견 기록 사진";


                card.appendChild(
                    image
                );

            }


            historyList.appendChild(
                card
            );

        }
    );

}