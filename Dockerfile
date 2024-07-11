FROM python:3.12-alpine as base
FROM base as builder
RUN pip install --user fastapi pyotp

FROM base
# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app

# update PATH environment variable
ENV PATH=/root/.local/bin:$PATH
# RUN ls -la /root/.local/bin

CMD ["fastapi", "run", "main.py"]