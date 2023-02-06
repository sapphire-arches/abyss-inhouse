package pw.cakesoft.abyss;

import java.util.HashMap;

import skadistats.clarity.io.Util;
import skadistats.clarity.model.Entity;
import skadistats.clarity.model.FieldPath;
import skadistats.clarity.processor.entities.Entities;
import skadistats.clarity.processor.entities.UsesEntities;
import skadistats.clarity.processor.reader.OnMessage;
import skadistats.clarity.processor.reader.OnTickStart;
import skadistats.clarity.processor.runner.Context;
import skadistats.clarity.processor.runner.SimpleRunner;
import skadistats.clarity.processor.stringtables.UsesStringTable;
import skadistats.clarity.source.MappedFileSource;
import skadistats.clarity.source.Source;
import skadistats.clarity.wire.common.proto.DotaUserMessages;
import skadistats.clarity.wire.s2.proto.S2UserMessages;

/**
 * Hello world!
 *
 */
public class App {
	private final HashMap<Integer, Long> playerIDs = new HashMap();
	private final HashMap<Long, String> latestPlayerId = new HashMap();
	private final HashMap<Long, Integer> numTips = new HashMap();
	private boolean init = false;

	public <T> T getEntityProperty(Entity e, String property, Integer idx) {
		try {
			if (e == null) {
				return null;
			}
			if (idx != null) {
				property = property.replace("%i", Util.arrayIdxToString(idx));
			}
			FieldPath fp = e.getDtClass().getFieldPathForName(property);
			return e.getPropertyForFieldPath(fp);
		} catch (Exception ex) {
			return null;
		}
	}

	@OnMessage(S2UserMessages.CUserMessageSayText2.class)
	public void onMessage(Context ctx, S2UserMessages.CUserMessageSayText2 message) {
		System.out.format("%s: %s\n", message.getParam1(), message.getParam2());
	}

	@OnMessage(DotaUserMessages.CDOTAUserMsg_TipAlert.class)
	public void onTip(DotaUserMessages.CDOTAUserMsg_TipAlert message) {
		System.out.format("Got tip: %s\n", message.getPlayerId());
	}

	@OnMessage(DotaUserMessages.CDOTAUserMsg_HeroRelicProgress.class)
	public void onHeroRelic(DotaUserMessages.CDOTAUserMsg_HeroRelicProgress message) {
		System.out.format("Got relic? %s\n", message.getAllFields());
	}

	@OnMessage(DotaUserMessages.CDOTAUserMsg_SalutePlayer.class)
	@UsesEntities
	public void onSalute(Context ctx, DotaUserMessages.CDOTAUserMsg_SalutePlayer message) {
		Entity pd = ctx.getProcessor(Entities.class).getByDtName("CDOTA_PlayerResource");

		int sourcePlayerId = message.getSourcePlayerId();
		String sourcePlayerName = getEntityProperty(pd, "m_vecPlayerData.%i.m_iszPlayerName",
				sourcePlayerId);
		Long sourcePlayerSteamID = getEntityProperty(pd, "m_vecPlayerData.%i.m_iPlayerSteamID",
				sourcePlayerId);
		
		this.latestPlayerId.put(sourcePlayerSteamID, sourcePlayerName);
		
		int targetPlayerId = message.getTargetPlayerId();
		String targetPlayerName = getEntityProperty(pd, "m_vecPlayerData.%i.m_iszPlayerName",
				targetPlayerId);
		Long targetPlayerSteamID = getEntityProperty(pd, "m_vecPlayerData.%i.m_iPlayerSteamID",
				targetPlayerId);
		
		this.latestPlayerId.put(targetPlayerSteamID, targetPlayerName);
		
		System.out.format("Player %s:%s saluted by player %s:%s\n", sourcePlayerId, sourcePlayerName,
				targetPlayerId, targetPlayerName);
		
		this.numTips.put(targetPlayerSteamID, this.numTips.getOrDefault(targetPlayerSteamID, 0) + 1);
	}

	public static void main(String[] args) throws Exception {
		App processor = new App();
		for (String s : args) {
			System.out.format("Process replay %s\n", s);
			Source source = new MappedFileSource(s);
			SimpleRunner runner = new SimpleRunner(source);
			runner.runWith(processor);
		}
		
		for (Long steamID : processor.numTips.keySet()) {
			String name = processor.latestPlayerId.get(steamID);
			System.out.format("%32s %s: %s\n", name, steamID, processor.numTips.get(steamID));
		}
	}
}
