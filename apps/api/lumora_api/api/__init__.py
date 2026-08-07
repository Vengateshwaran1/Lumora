"""HTTP/SSE transport layer — routers only, no business logic.

Routers translate requests into calls against the `application` layer and
translate results back into responses; they must not contain business rules
themselves.
"""
