// Firebase setup
import { initializeApp } from "firebase/app";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth";

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyCV1eQPefV4Uxje-WvZoWHyF0P79GTQb-s",
  authDomain: "login-form-717c3.firebaseapp.com",
  projectId: "login-form-717c3",
  storageBucket: "login-form-717c3.firebasestorage.app",
  messagingSenderId: "107346948786",
  appId: "1:107346948786:web:2aa910d60a8b979e998fab"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Handle Login
document.getElementById('loginForm')?.addEventListener('submit', function (e) {
  e.preventDefault();

  const email = document.getElementById('email')?.value;
  const password = document.getElementById('password')?.value;

  signInWithEmailAndPassword(auth, email, password)
    .then((userCredential) => {
      alert("✅ Login successful!");
      console.log(userCredential.user);
    })
    .catch((error) => {
      alert("❌ Login failed: " + error.message);
    });
});

// Handle Signup
document.getElementById("signupForm").addEventListener("submit", function (e) {
    e.preventDefault(); // prevents the form from refreshing the page
  
    console.log("Signup form submitted"); // ✅ Add this here to confirm it's working
  
    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
  
    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
  
    // Firebase signup
    firebase.auth().createUserWithEmailAndPassword(email, password)
      .then((userCredential) => {
        console.log("Signup successful:", userCredential.user);
      })
      .catch((error) => {
        console.error("Signup error:", error);
        alert(error.message);
      });
  });