// Based on https://github.com/discord/discord-example-app/blob/main/utils.js
import { Request, Response } from "express";
import { verifyKey } from "discord-interactions";
import { Axios } from "axios";

export function VerifyDiscordRequest(clientKey: string) {
  return function (req: Request, res: Response, buf: Buffer, encoding: string) {
    const signature = req.get("X-Signature-Ed25519");
    const timestamp = req.get("X-Signature-Timestamp");

    if (signature === undefined) {
      const err = "Missing X-Signature-Ed25519 header";
      res.status(400).send(err);
      throw new Error(err);
    }

    if (timestamp === undefined) {
      const err = "Missing X-Signature-Timestamp header";
      res.status(400).send(err);
      throw new Error(err);
    }

    const isValidRequest = verifyKey(buf, signature, timestamp, clientKey);
    if (!isValidRequest) {
      res.status(401).send("Bad request signature");
      throw new Error("Bad request signature");
    }
  };
}

type DiscordRequestOptions = {
  method: string;
  body?: any;
};

export const Session = new Axios({
  baseURL: 'https://discord.com/api/v10/',
  headers: {
    'Authorization': `Bot ${process.env.DISCORD_TOKEN}`,
    'Content-Type': 'application/json; charset=UTF-8',
    'User-Agent': 'DiscordBot (https://github.com/bobtwinkles/abyss-inhouse, 1.0.0)',
  },
  transformResponse: [function (data) {
    return JSON.parse(data);
  }],
  transformRequest: [ function(data) {
    return JSON.stringify(data);
  }],
})

export const APP_ID = process.env.APP_ID;
