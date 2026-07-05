# Authentication Research

## Authentication vs Authorization

Authentication answers:

> Who are you?

Authorization answers:

> What are you allowed to do?

---

# Why Passwords Shouldn't Be Sent on Every Request

Sending a password with every API request is insecure and inefficient.

Instead, after successful authentication, the server issues a signed token.

The client presents this token on future requests.

This is similar to receiving a wristband after entering a carnival.

---

# JSON Web Tokens (JWT)

A JWT is a digitally signed token that proves a user's identity.

It typically contains:

- User ID
- Expiration time
- Claims
- Digital signature

The signature prevents users from modifying the token.

---

# Firebase Authentication

Firebase Authentication simplifies user authentication.

After login:

- Firebase verifies the credentials.
- Firebase issues an ID Token (JWT).
- Flutter stores the token.
- FastAPI verifies the token before serving protected endpoints.

---

# Planned Research

Topics to explore further:

- Firebase Admin SDK
- JWT verification
- Refresh tokens
- Role-Based Access Control (RBAC)