export class AppError extends Error {
  constructor(message, status = 500) {
    super(message);
    this.status = status;

    Error.captureStackTrace(this, this.constructor);
  }
}