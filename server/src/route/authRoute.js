import { Router } from "express";
import { login, signup } from "../service/authService.js";

const router = Router();

router.post("/signup", async (req, res, next) => {
  try {
    const { email, password } = req.body;

    const result = await signup(email, password);

    return res.status(201).json({
      message: "User created successfully",
      result,
    });
  } catch (error) {
    next(error);
  }
});

router.post("/login", async (req, res, next) => {
  try {
    const { email, password } = req.body;

    const result = await login(email, password);

    return res.status(200).json({
      message: "Login successful",
      result,
    });
  } catch (error) {
    next(error);
  }
});

export default router;