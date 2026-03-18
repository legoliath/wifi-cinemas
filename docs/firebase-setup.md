# Firebase Setup Guide

## 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Add project** → Name: `wifi-cinemas`
3. Enable Google Analytics (optional)

## 2. Enable Authentication
1. **Authentication** → **Sign-in method**
2. Enable: **Email/Password**, **Apple**, **Google**
3. **Settings** → **Authorized domains** → Add your API domain

## 3. Create Service Account (Backend)
1. **Project settings** → **Service accounts** → **Generate new private key**
2. Save as `firebase-service-account.json` (in `.gitignore`)
3. Copy to `api/firebase-service-account.json`

## 4. Configure iOS App
1. **Your apps** → **Add app** → iOS
2. Bundle ID: `com.wificinemas.app`
3. Download `GoogleService-Info.plist` → place in `mobile/ios/`

## 5. Configure Android App
1. **Add app** → Android
2. Package: `com.wificinemas.app`
3. Download `google-services.json` → place in `mobile/android/app/`

## 6. Cloud Messaging (Push)
### iOS
1. Apple Developer → Create APNs Authentication Key (.p8)
2. Firebase → **Cloud Messaging** → Upload APNs key

### Android
Enabled by default with `google-services.json`.

## 7. Environment Variables

| Variable | Location | Description |
|----------|----------|-------------|
| `FIREBASE_PROJECT_ID` | `api/.env` | Firebase project ID |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | `api/.env` | Path to service account JSON |
| `GoogleService-Info.plist` | `mobile/ios/` | iOS Firebase config |
| `google-services.json` | `mobile/android/app/` | Android Firebase config |

## 8. Test
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","name":"Test","password":"test123"}'
```
