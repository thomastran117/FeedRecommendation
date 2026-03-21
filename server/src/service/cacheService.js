import redis from "../resource/redis.js";

const DEFAULT_TTL = 60 * 5;

export const set = async (key, value, ttl = DEFAULT_TTL) => {
  const serialized = JSON.stringify(value);

  if (ttl) {
    await redis.set(key, serialized, {
      EX: ttl,
    });
  } else {
    await redis.set(key, serialized);
  }
};

export const get = async (key) => {
  const value = await redis.get(key);
  if (!value) return null;

  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
};

export const del = async (key) => {
  await redis.del(key);
};

export const exists = async (key) => {
  return (await redis.exists(key)) === 1;
};

export const expire = async (key, ttl) => {
  await redis.expire(key, ttl);
};

export const setNX = async (key, value, ttl = DEFAULT_TTL) => {
  const serialized = JSON.stringify(value);

  const result = await redis.set(key, serialized, {
    NX: true,
    EX: ttl,
  });

  return result === "OK";
};

export const incr = async (key) => {
  return redis.incr(key);
};

export const incrBy = async (key, amount) => {
  return redis.incrBy(key, amount);
};

export const ttl = async (key) => {
  return redis.ttl(key);
};

export const delByPattern = async (pattern) => {
  const keys = await redis.keys(pattern);
  if (keys.length === 0) return;

  await redis.del(keys);
};