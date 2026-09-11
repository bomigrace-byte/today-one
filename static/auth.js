// =========================================================
// Supabase Auth
// =========================================================

const SUPABASE_URL =
    "https://wdkorgbseawngzchavrw.supabase.co";

const SUPABASE_ANON_KEY =
    "sb_publishable_cPJxr0Adc5pzpXlDpPf7JA_Fk-sRHcc";


const supabaseClient =
    window.supabase.createClient(
        SUPABASE_URL,
        SUPABASE_ANON_KEY
    );


// =========================================================
// 요소
// =========================================================

const authScreen =
    document.getElementById("auth-screen");

const homeScreen =
    document.getElementById("home-screen");

const emailInput =
    document.getElementById("auth-email");

const passwordInput =
    document.getElementById("auth-password");

const loginButton =
    document.getElementById("login-button");

const signupButton =
    document.getElementById("signup-button");

const demoLoginButton =
    document.getElementById("demo-login-button");

const logoutButton =
    document.getElementById("logout-button");

const authMessage =
    document.getElementById("auth-message");


// =========================================================
// 인증된 Flask API 요청
// =========================================================

async function authenticatedFetch(url, options = {}) {

    const {
        data: {
            session
        }
    } =
        await supabaseClient.auth.getSession();


    const requestOptions = {
        ...options
    };


    const headers = {
        ...(options.headers || {})
    };


    if (session && session.access_token) {

        headers["Authorization"] =
            "Bearer " + session.access_token;
    }


    requestOptions.headers = headers;


    return window.fetch(
        url,
        requestOptions
    );
}


window.authenticatedFetch =
    authenticatedFetch;


// =========================================================
// 메시지
// =========================================================

function showAuthMessage(message) {

    authMessage.textContent =
        message;
}


// =========================================================
// 화면 전환
// =========================================================

function showLoggedIn() {

    authScreen.classList.add(
        "hidden"
    );

    homeScreen.classList.remove(
        "hidden"
    );
}


function showLoggedOut() {

    authScreen.classList.remove(
        "hidden"
    );

    homeScreen.classList.add(
        "hidden"
    );
}


// =========================================================
// 로그인
// =========================================================

loginButton.addEventListener(
    "click",
    async function () {

        const email =
            emailInput.value.trim();

        const password =
            passwordInput.value;


        if (!email || !password) {

            showAuthMessage(
                "이메일과 비밀번호를 입력해주세요."
            );

            return;
        }


        loginButton.disabled = true;

        showAuthMessage(
            "로그인 중..."
        );


        try {

            const {
                data,
                error
            } =
                await supabaseClient.auth.signInWithPassword({
                    email: email,
                    password: password
                });


            if (error) {

                console.error(
                    "Supabase 로그인 오류:",
                    error
                );

                showAuthMessage(
                    `로그인 실패: ${error.message}`
                );

                return;
            }


            if (!data || !data.session) {

                showAuthMessage(
                    "로그인 세션을 만들지 못했습니다."
                );

                return;
            }


            showAuthMessage("");

            showLoggedIn();


            window.dispatchEvent(
                new Event("auth-ready")
            );

        } catch (error) {

            console.error(
                "로그인 처리 중 오류:",
                error
            );

            showAuthMessage(
                `로그인 실패: ${error.message}`
            );

        } finally {

            loginButton.disabled = false;
        }
    }
);


// =========================================================
// 회원가입
// =========================================================

signupButton.addEventListener(
    "click",
    async function () {

        const email =
            emailInput.value.trim();

        const password =
            passwordInput.value;


        if (!email || !password) {

            showAuthMessage(
                "이메일과 비밀번호를 입력해주세요."
            );

            return;
        }


        if (password.length < 6) {

            showAuthMessage(
                "비밀번호는 6자 이상 입력해주세요."
            );

            return;
        }


        signupButton.disabled = true;

        showAuthMessage(
            "회원가입 중..."
        );


        try {

            const {
                data,
                error
            } =
                await supabaseClient.auth.signUp({
                    email: email,
                    password: password
                });


            if (error) {

                console.error(
                    "Supabase 회원가입 오류:",
                    error
                );

                showAuthMessage(
                    `회원가입 실패: ${error.message}`
                );

                return;
            }


            if (!data || !data.session) {

                showAuthMessage(
                    "회원가입이 완료되었습니다. 이메일로 받은 인증 링크를 확인한 뒤 로그인해주세요."
                );

                return;
            }


            showAuthMessage("");

            showLoggedIn();


            window.dispatchEvent(
                new Event("auth-ready")
            );

        } catch (error) {

            console.error(
                "회원가입 처리 중 오류:",
                error
            );

            showAuthMessage(
                `회원가입 실패: ${error.message}`
            );

        } finally {

            signupButton.disabled = false;
        }
    }
);


// =========================================================
// 데모 계정
// =========================================================

demoLoginButton.addEventListener(
    "click",
    function () {

        emailInput.value =
            "demo@today-one.com";

        passwordInput.value =
            "TodayOneDemo2026!";


        loginButton.click();
    }
);


// =========================================================
// 로그아웃
// =========================================================

logoutButton.addEventListener(
    "click",
    async function () {

        await supabaseClient.auth.signOut();

        window.location.reload();
    }
);


// =========================================================
// 로그인 상태 확인
// =========================================================

async function checkAuth() {

    try {

        const {
            data: {
                session
            }
        } =
            await supabaseClient.auth.getSession();


        if (session) {

            showLoggedIn();

            window.dispatchEvent(
                new Event("auth-ready")
            );

            return;
        }


        showLoggedOut();

    } catch (error) {

        console.error(
            "Auth 상태 확인 오류:",
            error
        );

        showLoggedOut();
    }
}


checkAuth();


// =========================================================
// 인증 상태 변경 감지
// =========================================================

supabaseClient.auth.onAuthStateChange(
    function (
        event,
        session
    ) {

        console.log(
            "Auth 상태:",
            event
        );


        if (session) {

            showLoggedIn();

        } else {

            showLoggedOut();
        }
    }
);