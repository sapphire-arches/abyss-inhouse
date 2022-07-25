import {
  InteractionType,
  InteractionResponseFlags,
  MessageComponentTypes,
  ButtonStyleTypes,
} from "discord-interactions";
import express, { Request, Response } from "express";
import { VerifyDiscordRequest } from "./util.js";
import { GuildCommand } from "./commands.js";
import { ApplicationCommandType, APIInteractionResponse, InteractionResponseType, APIInteractionResponseChannelMessageWithSource } from "discord-api-types/v10";
import { SpanStatusCode, trace } from "@opentelemetry/api";

const COMMANDS = [
  new GuildCommand({
    name: 'test',
    type: ApplicationCommandType.ChatInput,
    description: "Test command",
  }),
];

const app = express();

const PORT = process.env.PORT || 3000;

const REQUIRED_VARS = [
  'APP_ID',
  'DISCORD_TOKEN',
  'PUBLIC_KEY',
];

REQUIRED_VARS.forEach((key) => {
  if (process.env[key] === undefined) {
    console.error(`${key} must be set in the environment`);
    // Exit 2 will also kill nodemon, so we can restart it in the right
    // environment.
    process.exit(2);
  }
});

app.use(
  express.json({
    verify: VerifyDiscordRequest(process.env.PUBLIC_KEY!),
  })
);

app.get('/', async function(req, res) {
  res.status(200).send("hello, world");
});

async function handleAppCommand(req: Request, res: Response) : Promise<APIInteractionResponseChannelMessageWithSource> {
  return {
    type: InteractionResponseType.ChannelMessageWithSource,
    data: {
      content: 'hi!',
    },
  };
}

app.post('/interactions', async function(req, res) {
  const {type, id, data } = req.body;
  const tracer = trace.getTracer('discord');

  return await tracer.startActiveSpan('discord.interaction',
    {
      attributes: {
        type: type,
        id: id,
      }
    }, async (span) => {
      var result: APIInteractionResponse | null = null;
      try {
        if (type === InteractionType.PING) {
          result = { type: InteractionResponseType.Pong };
        }

        if (type === InteractionType.APPLICATION_COMMAND) {
          result = await handleAppCommand(req, res);
        }

        if (type === InteractionType.MESSAGE_COMPONENT) {
          // TODO
        }

        res.send(result);
        span.setStatus ({ code: SpanStatusCode.OK });

        span.end();
      } catch (err: any) {
        span.recordException(err);
        span.setStatus({ code: SpanStatusCode.ERROR });
        span.end();
        throw err;
      }
      return result;
  }).catch((err) => {
    console.error(`Failed to handle /interactions request: ${err}`);
  });
});

app.listen(PORT, () => {
  console.info(`Booted express at http://localhost:${PORT}`);

  COMMANDS.forEach((command: GuildCommand) => {
    command.register('1000819141596414002').catch((err) => {
      console.error(`Command ${command.slug} failed to register: ${err}`);
    });
  });
});

