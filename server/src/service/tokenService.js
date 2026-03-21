import jwt from "jsonwebtoken";
import crypto from "crypto";
import * as cache from "./cacheService.js";

const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET || "supersecret";
const ACCESS_TOKEN_EXPIRES_IN = process.env.ACCESS_TOKEN_EXPIRES_IN || "15m";
const REFRESH_TOKEN_TTL_SECONDS = Number(
  process.env.REFRESH_TOKEN_TTL_SECONDS || 60 * 60 * 24 * 7
);

if (!ACCESS_SECRET) {
  throw new Error("JWT_ACCESS_SECRET is not configured");
}

const getRefreshTokenKey = (token) => `auth:refresh:${token}`;
const getUserRefreshTokensKey = (userId) => `auth:user_refresh_tokens:${userId}`;

export const createAccessToken = (userId) => {
  return jwt.sign(
    { sub: String(userId), type: "access" },
    ACCESS_SECRET,
    { expiresIn: ACCESS_TOKEN_EXPIRES_IN }
  );
};

export const verifyAccessToken = (token) => {
  const payload = jwt.verify(token, ACCESS_SECRET);

  if (payload.type !== "access") {
    throw new Error("Invalid access token");
  }

  return {
    userId: Number(payload.sub),
    payload,
  };
};

export const createRefreshToken = async (userId) => {
  const token = crypto.randomBytes(48).toString("hex");
  const refreshKey = getRefreshTokenKey(token);
  const userTokensKey = getUserRefreshTokensKey(userId);

  await cache.set(
    refreshKey,
    {
      userId,
      type: "refresh",
    },
    REFRESH_TOKEN_TTL_SECONDS
  );

  await cache.add(userTokensKey, token);
  await cache.expire(userTokensKey, REFRESH_TOKEN_TTL_SECONDS);

  return token;
};

export const verifyRefreshToken = async (token) => {
  const refreshKey = getRefreshTokenKey(token);
  const data = await cache.get(refreshKey);

  if (!data) {
    throw new Error("Invalid or expired refresh token");
  }

  if (data.type !== "refresh") {
    throw new Error("Invalid refresh token");
  }

  return {
    userId: Number(data.userId),
    token,
  };
};

export const logout = async (token) => {
  const refreshKey = getRefreshTokenKey(token);
  const data = await cache.get(refreshKey);

  if (data?.userId) {
    const userTokensKey = getUserRefreshTokensKey(data.userId);
    await cache.srem(userTokensKey, token);
  }

  await cache.del(refreshKey);
  return true;
};

export const rotateRefreshToken = async (oldToken) => {
  const { userId } = await verifyRefreshToken(oldToken);

  await logout(oldToken);

  const accessToken = createAccessToken(userId);
  const refreshToken = await createRefreshToken(userId);

  return {
    accessToken,
    refreshToken,
    userId,
  };
};

export const logoutAll = async (userId) => {
  const userTokensKey = getUserRefreshTokensKey(userId);
  const tokens = await cache.smembers(userTokensKey);

  for (const token of tokens) {
    await cache.del(getRefreshTokenKey(token));
  }

  await cache.del(userTokensKey);
  return true;
};