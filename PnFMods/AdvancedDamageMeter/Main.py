API_VERSION = 'API_v1.0'

MOD_NAME = 'AdvancedDamageMeter'

try:
    import battle, events, ui
except:
    pass

MAX_LOGS_COUNT = 10

COMPONENT_KEY_INCOMING = 'modAdvancedDamageMeterIncomingDamage'
COMPONENT_KEY_OUTGOING = 'modAdvancedDamageMeterOutgoingDamage'

AMMO_TYPE_TO_ICON_NAME = {
    'AP': 'main_caliber',
    'HE': 'main_caliber',
    'CS': 'main_caliber',
    'SECTOR_WAVE': 'wave',
    'impulseLaser': 'laser',
    'chargeLaser': 'laser',
    'axisLaser': 'laser',
    'seaMine': 'naval_mine',
    'mine': 'mine',
    'skip': 'skip',
    'depthcharge': 'depthbomb',
    'torpedo': 'torpedo',
    'bomb': 'bomb',
    'rocket': 'rocket',
}


class AdvancedDamageMeter(object):

    def __init__(self):
        events.onReceiveShellInfo(self.onReceiveShellInfo)
        events.onBattleStart(self.onBattleStart)
        events.onBattleQuit(self.onBattleQuit)

    def onReceiveShellInfo(self, victimId, shooterId, ammoId, matId, shotId, booleans, damage, shotPosition, yaw, hlinfo):
        # skip shots without damage
        if damage < 1:
            return
        
        victim = battle.getPlayerByVehicleId(victimId)
        shooter = battle.getPlayerByVehicleId(shooterId)
        player = battle.getSelfPlayerInfo()

        if victim is None or shooter is None:
            # Fortress/Airfields in Scenario mode:
            # PlayersInfo for these structures is None
            # 
            # Showing damage to them is possible, but
            # Their names are not accessible from Python API
            #
            # ToDo: Pass the entity ID to Unbound and let datahub search for the player/building and tags
            return

        damagedPlayer = shooter if player.shipId == victim.shipId else victim
        damageLog = self.__getDamageLog(ammoId, damage, damagedPlayer)

        if player.shipId == victimId:
            self.incomingDamageLogs.update(damageLog)
        elif player.shipId == shooterId:
            self.outgoingDamageLogs.update(damageLog)

    def __getDamageLog(self, ammoId, damage, damagedPlayer):
        """
        Get info about damage (will be sent to flash)
        :type ammoId: long
        :type damage: float
        :type damagedPlayer: PlayerInfo.PlayerInfo
        :return:
        """
        data = self.__getPlayerData(damagedPlayer)
        data['ammoType'] = self.__getAmmoName(ammoId)
        data['lastDamage'] = damage
        data['totalDamage'] = damage
        return data

    def __getPlayerData(self, player):
        """
        Create dict with information about player.
        :type player: PlayerInfo.PlayerInfo
        :rtype: dict
        """
        info = dict(
            victimId=player.id,
            playerName=player.name,
            clanTag=player.clanTag,
            subtype=player.shipInfo.subtype,
            shipNameIDS=player.shipInfo.nameIDS,
        )
        return info

    def __getAmmoName(self, ammoId):
        """
        Get ammo type by ammo id
        :type ammoId: long
        :rtype: str
        """
        ammoType = None
        ammoInfo = battle.getAmmoParams(ammoId)
        try:
            ammoType = ammoInfo.planeAmmoType
        except:
            ammoType = ammoInfo.ammoType
        return AMMO_TYPE_TO_ICON_NAME.get(ammoType, None)

    def onBattleStart(self):
        self.incomingDamageLogs = DamageLogsController(isIncomingDamage=True)
        self.outgoingDamageLogs = DamageLogsController(isIncomingDamage=False)

    def onBattleQuit(self, arg):
        """
        Called when player leaves battle. Clean damage info here.
        :return:
        """
        self.incomingDamageLogs.kill()
        self.incomingDamageLogs = None
        self.outgoingDamageLogs.kill()
        self.outgoingDamageLogs = None


class DamageLogsController(object):
    def __init__(self, isIncomingDamage=True):
        key = COMPONENT_KEY_INCOMING if isIncomingDamage else COMPONENT_KEY_OUTGOING
        self.damageLogEntityId = ui.createUiElement()
        ui.addDataComponentWithId(self.damageLogEntityId, key, {'damageLogs': []})
        self._damageLogs = []

    def update(self, damageLog):
        currentLogs = self._damageLogs
        if len(currentLogs) > 0 and currentLogs[0]['victimId'] == damageLog['victimId']:
            damageLog['totalDamage'] += currentLogs[0]['totalDamage']
            currentLogs[0] = damageLog
        else:
            if len(currentLogs) >= MAX_LOGS_COUNT:
                currentLogs.pop()
            currentLogs.insert(0, damageLog)
        ui.updateUiElementData(self.damageLogEntityId, {'damageLogs': list(currentLogs)})

    def kill(self):
        ui.deleteUiElement(self.damageLogEntityId)
        self._damageLogs = None


advancedDamageMeter = AdvancedDamageMeter()
