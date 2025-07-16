## Resolving "Bad Request" Errors in Google OAuth

If you encounter a "Bad Request" error during file upload in IDCODE, follow these steps:

1. **Navigate to this project directory.**
2. **Delete the `token.json` file** located in `/cred/drive/`.
3. **Open your work account profile in Chrome.**
   - This ensures VS Code redirects authentication to the correct Google account.
4. **Run the authentication flow and grant access.**
   - A new `token.json` will be automatically generated in `/cred/drive/`.
5. **Use the contents of the new `token.json`** as needed for environment variables in your application.

---

### For New Clones

If you have just cloned this repository from GitHub:

- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create or configure your OAuth credentials.
- Download your `credentials.json` and place it in `/cred/drive/`.

---

**Note:**  
Always ensure your `credentials.json` and `token.json` files are kept secure and never committed to version