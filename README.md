# eCommerce — backend

REST API for a general-purpose online shop: JWT accounts with email
verification, product catalogue with categories, cart, orders, Stripe
Checkout payments, product reviews, and a staff dashboard API.

The React frontend is in a separate repo (eCommerce_frontend).

## Stack

- Python, Django 5.1, Django REST Framework, Simple JWT (refresh-token rotation; logout blacklists the refresh token)
- PostgreSQL (via `DATABASE_URL` or individual `DB_*` settings)
- Stripe Checkout (hosted payment page + signed webhook)
- Cloudinary for uploaded media (product images)
- SendGrid HTTP API for verification emails
- gunicorn (`Procfile`)

`requirements.txt` also lists Celery and Redis, and `docker-compose.yml`
starts a Redis container, but no code uses them yet.

## Architecture

Django apps:

| App | Endpoints under | Purpose |
|---|---|---|
| `users` | `/api/users/` | Register, email verification and resend, JWT login/refresh/logout, profile |
| `products` | `/api/products/` | Products (search/filter) and categories; create/update/delete for staff |
| `orders` | `/api/orders/` | Cart, order creation, Stripe checkout session, Stripe webhook, payment verification, shipping address update |
| `reviews` | `/api/reviews/` | Create reviews, list a product's reviews; users can only edit/delete their own |
| `core` | `/api/dashboard/` | Staff stats, order/user/product lists, order status updates |

Payment flow: `POST /api/orders/<id>/checkout/` creates a Stripe Checkout
Session and returns its URL. Stripe's `checkout.session.completed` webhook
(signature-verified with `STRIPE_WEBHOOK_SECRET`) marks the order paid;
`POST /api/orders/<id>/verify-payment/` re-checks the session with Stripe as a
fallback when the customer returns.

`docker-compose.yml` runs only the backing services for development
(Postgres 15 and Redis 7); the Django app itself runs outside Docker.
Deployment: a push to `main` triggers a GitHub Actions job that SSHes to a
DigitalOcean droplet and runs a `deploy.sh` kept on the server (not in this
repo).

## Running locally

```sh
docker compose up -d db
python -m venv venv
venv\Scripts\activate          # Windows; on macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Create a `.env` file in the repo root (loaded by python-dotenv; never commit
it). Variables read in `core/settings.py` and `users/views.py`:

- Django: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `FRONTEND_URL`
- Database: either `DATABASE_URL`, or `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
  (to match the Compose database: name `ecommerce`, user `postgres`, host `localhost`, port `5432`, and the password set in `docker-compose.yml`)
- Stripe: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- Cloudinary: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- SendGrid: `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`

Image uploads go to Cloudinary, so they need the Cloudinary variables even
locally. To test the webhook locally, use the Stripe CLI:
`stripe listen --forward-to localhost:8000/api/orders/webhook/`.

## Tests

```sh
python manage.py test
```

There are no tests yet: each app's `tests.py` is the empty Django stub.
