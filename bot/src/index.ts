import { startTracing } from "./tracing";

startTracing().then(() => {
  require('./app');
});
