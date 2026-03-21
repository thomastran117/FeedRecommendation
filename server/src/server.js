import express from 'express';
import auth from "./route/authRoute.js";
import { errorHandler } from "./middleware/errorHandler.js";

const app = express();
const PORT = 3000;

app.use(express.json());
app.use('/api/auth', auth); 

app.use(errorHandler);

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});