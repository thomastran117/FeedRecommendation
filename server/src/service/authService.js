import bcrypt from "bcrypt";
import prisma from "../resource/database.js";
import * as token from "./tokenService.js";
import { AppError } from "../utilities/error.js";

const SALT_ROUNDS = 10;

export const signup = async (email, password) => {
  const existingUser = await prisma.user.findUnique({
    where: { email },
  });

  if (existingUser) {
    throw new AppError("Email exists", 409);
  }

  const hashedPassword = await hashPassword(password);

  const user = await prisma.user.create({
    data: {
      email,
      password: hashedPassword,
    },
    select: {
      id: true,
      email: true
    },
  });

  const accessToken = await token.createAccessToken(user.id);
  const refreshToken = await token.createRefreshToken(user.id);

  return { accessToken, refreshToken};
};

export const login = async (email, password) => {
  const user = await prisma.user.findUnique({
    where: { email },
  });

  if (!user) {
    throw new AppError("Invalid email or password", 401);
  }

  const isValidPassword = await verifyPassword(user.password, password);

  if (!isValidPassword) {
    throw new AppError("Invalid email or password", 401);
  }

  const accessToken = await token.createAccessToken(user.id);
  const refreshToken = await token.createRefreshToken(user.id);

  return { accessToken, refreshToken};
};

export const hashPassword = async (password) => {
  return bcrypt.hash(password, SALT_ROUNDS);
};

export const verifyPassword = async (hashedPassword, password) => {
  return bcrypt.compare(password, hashedPassword);
};