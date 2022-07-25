import process from "process";
import { ExpressInstrumentation } from "@opentelemetry/instrumentation-express";
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";
import { NodeSDK, tracing } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
import { diag, DiagConsoleLogger, DiagLogLevel } from "@opentelemetry/api";

export async function startTracing() {
  diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.INFO);

  const traceExporter = new OTLPTraceExporter({
    url: 'http://jaeger-collector.default.svc.cluster.local:4317',
  });

  var telemetry = new NodeSDK({
    // traceExporter: new tracing.ConsoleSpanExporter(),
    traceExporter,
    instrumentations: [
      new HttpInstrumentation(),
      new ExpressInstrumentation(),
    ],
    serviceName: "discord-bot",
  });

  await telemetry
    .start()
    .then(() => {
      console.info("Tracing initialized")
    })
    .catch((error) => console.error("Error initializing tracing", error));

  ["SIGTERM", "SIGINT"].forEach((signal) => {
    process.on(signal, () => {
      telemetry
        .shutdown()
        .then(() => console.info("Shut down tracing"))
        .catch((error) => console.error("Error terminating tracing", error))
        .finally(() => process.exit(0));
    });
  });
}
