import { APP_ID, Session } from './util.js';
import { SpanStatusCode, trace } from '@opentelemetry/api';
import { RESTGetAPIApplicationGuildCommandsResult, RESTPostAPIChatInputApplicationCommandsJSONBody } from "discord-api-types/v10";

async function fetchCommands(guild: string) : Promise<RESTGetAPIApplicationGuildCommandsResult> {
  const tracer = trace.getTracer('discord');

  const endpoint = `applications/${APP_ID}/guilds/${guild}/commands`;

  return tracer.startActiveSpan('discord.fetchCommands', async (span) => {
    try {
      const res = await Session.get(endpoint);
      const data: RESTGetAPIApplicationGuildCommandsResult = res.data;

      if (data) {
        span.end();
        return data;
      } else {
        throw new Object();
      }
    } catch (err: any) {
      span.recordException(err);
      span.setStatus({ code: SpanStatusCode.ERROR });
      span.end();
      throw err;
    }
  });
}

export class GuildCommand {
  slug: string;
  spec: RESTPostAPIChatInputApplicationCommandsJSONBody;

  constructor(spec: RESTPostAPIChatInputApplicationCommandsJSONBody) {
    this.slug = spec.name;
    this.spec = spec;
  }

  async register(guild: string) {
    const tracer = trace.getTracer('discord');
    const cmd = this;

    return await tracer.startActiveSpan('discord.installCommand',
      {
        attributes: {
          'command': cmd.slug,
          'guild': guild,
        }
      },
      (async (span) => {
        const commands = await fetchCommands(guild);

        const command = commands.find(c => c.name === cmd.slug);

        if (command === undefined ||
            command.description != cmd.spec.description
            ) {
          await Session.post(
            `applications/${APP_ID}/guilds/${guild}/commands`,
            cmd.spec,
          );
        }

        span.end();
      })
    );
  }
}
