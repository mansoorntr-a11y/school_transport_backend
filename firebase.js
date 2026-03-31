const admin = require("firebase-admin");

// This pulls the secret key you'll add to the Render Dashboard
const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  // Get this URL from your Firebase Console (Project Settings)
  databaseURL: "https://fleettrackpro-7017f.firebaseio.com" 
});

const db = admin.firestore();
module.exports = { db };