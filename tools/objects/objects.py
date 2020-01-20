import random
import re
from datetime import datetime
from pathlib import Path
from time import time as timestamp
from typing import List, Optional

import yaml

from .base import userlist_dist, LoultObject, cooldown, destructible, targeted, inert, clonable
from ..effects.effects import ExplicitTextEffect, GrandSpeechMasterEffect, StutterEffect, VocalDyslexia, \
    VowelExchangeEffect, FlowerEffect, CaptainHaddockEffect
from ..tools import cached_loader

DATA_PATH = Path(__file__).absolute().parent / Path("data")


@inert
@clonable
class DiseaseObject(LoultObject):
    DISEASES = ["syphilis", "diarrhée", "chaude-pisse", "gripe aviaire"]

    def __init__(self, patient_zero, disease=None):
        super().__init__()
        if disease is None:
            self.disease = random.choice(self.DISEASES)
        self.patient_zero = patient_zero

    @property
    def name(self):
        return "la %s de %s" % (self.disease, self.patient_zero)


@destructible
class Flower(LoultObject):
    ICON = "flower.gif"
    FLOWERS = ["rose", "lys blanc", "iris", "chrysanthème", "oeillet", "jonquille", "muguet",
               "tulipe", "orchidée"]

    def __init__(self):
        super().__init__()
        self.flower_name = random.choice(self.FLOWERS)
        self.remaining_uses = int(random.uniform(3, 6))

    @property
    def name(self):
        return self.flower_name

    def use(self, obj_params):
        if self.remaining_uses == 0:
            msg = "cette fleur est complètement fanée."
            self.notify_serv(msg=msg)
            self.should_be_destroyed = True
        else:
            name = self.user.poke_params.fullname
            msg = "{name} met une fleur dans ses cheveux, c twe miwmiw."
            self.channel.broadcast(type="notification", msg=msg.format(name=name))
            self.user.state.add_effect(FlowerEffect())
            self.remaining_uses -= 1


@destructible
class BaseballBat(LoultObject):
    ICON = "baseballbat.gif"
    FIGHTING_FX_DIR = DATA_PATH / Path("fighting/")
    BROKEN_BAT_FX = DATA_PATH / Path("broken_bat.mp3")
    INSERTION_FX = DATA_PATH / Path("baseball_bat_insertion.mp3")

    def __init__(self, target_userid, target_username):
        super().__init__()
        self.lynched_name = target_username
        self.lynched_userid = target_userid
        self.remaining_hits = random.randint(5, 15)
        self.sounds = []
        for filename in self.FIGHTING_FX_DIR.iterdir():
            self.sounds.append(cached_loader.load_byte(str(filename)))

    @property
    def name(self):
        return "Batte pour frapper %s" % self.lynched_name

    def use(self, obj_params):
        # checking if target user is present, sending a notif and a sound
        if self.lynched_userid in self.channel.users:
            if self.remaining_hits > 0:
                self.notify_channel(msg=f"{self.user_fullname} donne un coup de batte à {self.lynched_name}",
                                    binary_payload=random.choice(self.sounds))
            self.remaining_hits -= 1
        else:
            self.notify_channel(msg=f"{self.user_fullname} s'insère une batte de baseball au fond des muqueuses!",
                                binary_payload=self._load_byte(self.INSERTION_FX))
            self.should_be_destroyed = True

        # if it's the last hit, notifying and destroying the object
        if self.remaining_hits <= 0:
            self.should_be_destroyed = True
            self.notify_channel(msg=f"{self.user_fullname} a cassé sa batte sur {self.lynched_name}",
                                binary_payload=cached_loader.load_byte(str(self.BROKEN_BAT_FX)))


@destructible
class Crown(LoultObject):
    NAME = "Couronne du loult"
    ICON = "crown.gif"

    class ServantEffect(ExplicitTextEffect):
        TIMEOUT = 300
        SUFFIXES = ["seigneur %s", "maître %s", "mon roi", "mon bon %s", "ô grand %s", "sire %s",
                    "sieur %s", "vénérable %s", "%s, roi du loult", "%s maître des bibwe"]

        def __init__(self, pokename):
            super().__init__()
            self.suffixes = [suff % pokename if "%s" in suff else suff for suff in self.SUFFIXES]

        def process(self, text: str):
            return text.strip("!,.:?") + ", " + random.choice(self.suffixes)

    def use(self, obj_params):
        for user in self.channel.users.values():
            if user is not self.user:
                user.state.add_effect(self.ServantEffect(self.user.poke_params.pokename))
        self.notify_channel(msg=f"{self.user_fullname} est maintenant le roi du loult")
        self.should_be_destroyed = True


@targeted()
@destructible
class ScrollOfQurk(LoultObject):
    NAME = "Parchemin du Qurk"
    ICON = "parchemin.gif"
    FX_FILE = DATA_PATH / Path("magic_spell.mp3")

    class DuckEffect(ExplicitTextEffect):
        TIMEOUT = 300

        def process(self, text: str):
            return re.sub(r"[\w]+", "qurk", text)

    def use(self, obj_params):
        if random.randint(1, 5) == 1:
            target = self.user
            msg = f"{self.user_fullname} a mal lu le parchemin du Qurk et s'est changé en canard!"
        else:
            target = self.targeted_user
            msg = f"{self.user_fullname} a changé {target.poke_params.fullname} en canard!"
        self.notify_channel(msg=msg, binary_payload=self._load_byte(self.FX_FILE))
        target.state.add_effect(self.DuckEffect())
        params = target.poke_params
        params.img_id = "qurk"
        params.pokename = "Qurkee"
        target._info = None
        self.channel.update_userlist()
        self.should_be_destroyed = True


@targeted()
@destructible
class Scolopamine(LoultObject):
    NAME = "Scolopamine"
    ICON = "scolopamine.gif"

    def use(self, obj_params):
        self.user.state.inventory.objects += self.targeted_user.state.inventory.objects
        self.targeted_user.state.inventory.objects = []
        self.targeted_user.state.add_effect(GrandSpeechMasterEffect())

        self.notify_channel(
            msg=f"{self.user.poke_params.fullname} a drogué {self.targeted_user.poke_params.fullname} et puis a piqué tout son inventaire!")
        self.should_be_destroyed = True


@destructible
@targeted(mandatory=False)
class AlcoholBottle(LoultObject):
    NAME = "Bouteille d'alcool"
    ICON = "alcohol.gif"
    EFFECTS = [GrandSpeechMasterEffect, StutterEffect, VocalDyslexia, VowelExchangeEffect]
    FILLING_MAPPING = {0: "vide", 1: "presque vide", 2: "moitié vide",
                       3: "presque pleine", 4: "pleine"}
    BOTTLE_FX = DATA_PATH / Path("broken_bottle.mp3")
    GULP_FX = DATA_PATH / Path("gulp.mp3")
    ALCOHOLS = yaml.safe_load(open(DATA_PATH / Path("alcohols.yml")))

    def __init__(self):
        super().__init__()
        self.remaining_use = 4
        rnd_alc = random.choice(self.ALCOHOLS)
        self.alc_type = rnd_alc["name"]
        self.alc_brand = random.choice(rnd_alc["brands"])

    @property
    def name(self):
        if self.alc_type:
            return "Bouteille de %s %s (%s)" % (self.alc_type, self.alc_brand,
                                                self.FILLING_MAPPING[self.remaining_use])
        else:
            return "Bouteille de %s (%s)" % (self.alc_brand, self.FILLING_MAPPING[self.remaining_use])

    def use(self, obj_params):
        # user decides to use it on someone else, meaning throwing it
        if self.targeted_user is not None:
            target_dist = userlist_dist(self.channel, self.user.user_id, self.targeted_userid)
            if target_dist > 1:
                self.notify_serv(msg="Trop loin pour lancer la bouteille dessus!")
                return

            if self.targeted_user is self.user:
                msg = f"{self.user_fullname} se casse une {self.name} su'l'crâne!"
            else:
                msg = f"{self.user.poke_params.fullname} lance une {self.name} sur {self.targeted_user.poke_params.fullname}!"

            self.notify_channel(msg=msg, binary_payload=self._load_byte(self.BOTTLE_FX))
            self.targeted_user.disconnect_all_clients(code=4006, reason="Reconnect please")
            self.should_be_destroyed = True
        else:
            if self.remaining_use <= 0:
                return self.notify_serv(msg="La bouteille est vide!")
            self.notify_channel(msg=f"{self.user.poke_params.fullname} se descend un peu de {self.alc_brand}!",
                                binary_payload=self._load_byte(self.GULP_FX))
            for effect_type in self.EFFECTS:
                self.user.state.add_effect(effect_type())
            self.remaining_use -= 1


class Microphone(LoultObject):
    MIKEDROP_FX = DATA_PATH / Path("mikedrop.mp3")
    NAME = 'micro'
    ICON = "micro.gif"

    def use(self, obj_params):
        self.notify_channel(msg=f"{self.user.poke_params.fullname} drop le mike!",
                            binary_payload=self._load_byte(self.MIKEDROP_FX))
        self.user.disconnect_all_clients(code=4006, reason='Mike drop, bitch')


@inert
class C4(LoultObject):
    NAME = "C4"
    ICON = "c4.gif"


@destructible
class Detonator(LoultObject):
    NAME = "Détonateur"
    ICON = "detonator.gif"
    EXPLOSION_FX = DATA_PATH / Path("explosion.mp3")
    DETONATOR_CLICK_FX = DATA_PATH / Path("detonator_switch.mp3")

    def use(self, obj_params):
        if random.randint(1, 6) == 1:
            self.notify_channel(f"{self.user_fullname} a mal réglé son détonateur et s'est fait sauter",
                                binary_payload=self._load_byte(self.EXPLOSION_FX))
            self.user.disconnect_all_clients(4006, "Reconnect please")
            self.should_be_destroyed = True
            return

        blown_up_users = []
        for user in self.channel.users.values():
            if user.state.inventory.search_by_class(C4):
                user.state.inventory.remove_by_class(C4)
                for client in user.clients:
                    client.send_json(type="notification",
                                     msg="%s vous a fait sauter" % self.user.poke_params.fullname)
                    client.send_binary(self._load_byte(self.EXPLOSION_FX))
                    client.sendClose(code=4006, reason='reconnect later')
                blown_up_users.append(user.poke_params.fullname)
        if blown_up_users:
            self.notify_channel(msg=f"{self.user_fullname} a fait sauter {', '.join(blown_up_users)}!",
                                binary_payload=self._load_byte(self.EXPLOSION_FX))
        else:
            self.server.send_binary(self._load_byte(self.DETONATOR_CLICK_FX))


@destructible
class SuicideJacket(LoultObject):
    NAME = "ceinture d'explosif"
    ICON = "suicide.gif"
    EXPLOSION_FX = DATA_PATH / Path("suicide_bomber.mp3")

    def use(self, obj_params):
        hit_usrs = [usr for usr in self.channel.users.values()
                    if userlist_dist(self.channel, self.user.user_id, usr.user_id) < 3
                    and usr is not self.user]

        self.notify_serv(
            msg=f"{self.user.poke_params.fullname} s'est fait sauter, emportant avec lui {', '.join([usr.poke_params.fullname for usr in hit_usrs])}",
            bin_payload=self._load_byte(self.EXPLOSION_FX))
        self.channel.broadcast(type='antiflood', event='banned',
                               flooder_id=self.user.user_id,
                               date=timestamp() * 1000)
        self.loult_state.ban_ip(self.server.ip)
        self.user.disconnect_all_clients(code=4006, reason='Reconnect later')
        self.should_be_destroyed = True


@cooldown(30)
class Costume(LoultObject):
    NAME = "costume"

    CHARACTERS = ["link", "mario", "wario", "sonic"]

    def __init__(self):
        super().__init__()
        self.character: str = random.choice(self.CHARACTERS)

    @property
    def icon(self):
        return self.character + ".gif"

    @property
    def name(self):
        return self.NAME + " de %s" % self.character.capitalize()

    def use(self, obj_params):
        if hasattr(self.user, "costume") and self.user.costume == self.character:
            return self.notify_serv(
                msg="Vous ne pouvez pas enfiler deux fois d'affilée le costume!")

        self.notify_channel(msg=f"{self.user.poke_params.fullname} enfile un costume de {self.character.capitalize()}")
        params = self.user.poke_params
        params.img_id = self.character
        params.pokename = self.character.capitalize()
        self.user._info = None
        self.user.costume = self.character
        self.channel.update_userlist()


@targeted(mandatory=False)
@destructible
class RectalExam(LoultObject):
    NAME = "examen rectal"
    ICON = "rectalexam.gif"

    def use(self, obj_params):
        from ..objects import get_random_object
        rdm_objects = [get_random_object() for _ in range(random.randint(2, 4))]
        rdm_objects.append(Poop(self.targeted_user.poke_params.fullname))
        for obj in rdm_objects:
            self.user.state.inventory.add(obj)
        names_list = ", ".join(obj.name for obj in rdm_objects)

        if self.targeted_user is self.user:
            msg = f"{self.user.poke_params.fullname} a sorti {names_list} de son cul!"
        else:
            msg = f"{self.user_fullname} fouille dans le cul de {self.targeted_user.poke_params.fullname} et trouve {names_list}! "

        self.channel.broadcast(type="notification", msg=msg)
        self.should_be_destroyed = True


@targeted()
@cooldown(30)
class WealthDetector(LoultObject):
    NAME = "détecteur de richesse"
    ICON = "detector.gif"

    def use(self, obj_params):
        self.notify_channel(
            msg=f"{self.user_fullname} utilise le détecteur de richesse sur {self.targeted_user.poke_params.fullname}")
        self.notify_serv(
            msg=f"{self.targeted_user.poke_params.fullname} a {len(self.targeted_user.state.inventory.objects):d} objets dans son inventaire")


@destructible
@cooldown(5)
class Cigarettes(LoultObject):
    NAME = "cigarettes"
    ICON = "cigarettes.gif"
    BRANDS = ["Lucky Loult", "Lucky Loult Menthol", "Mrleboro", "Chesterfnre", "Sheitanes Maïs",
              "Aguloises"]
    CIG_FX = DATA_PATH / Path("cigarette_lighting.mp3")

    def __init__(self):
        super().__init__()
        self.brand = random.choice(self.BRANDS)
        self.cigarettes = 20

    @property
    def name(self):
        return self.brand + " (%i)" % self.cigarettes

    @property
    def destroy(self):
        return self.cigarettes <= 0

    def use(self, obj_params):
        if not self.user.state.inventory.search_by_class(Lighter):
            return self.notify_serv(
                msg="Il vous faut un briquet pour pouvoir allumer une clope!")

        self.cigarettes -= 1
        self.channel.broadcast(type="notification",
                               msg="%s allume une clope et prend un air cool"
                                   % self.user.poke_params.fullname,
                               binary_payload=self._load_byte(self.CIG_FX))
        if random.randint(1, 10) == 1:
            self.channel.broadcast(type="notification",
                                   msg="%s choppe le cancer et meurt sur le champ!"
                                       % self.user.poke_params.fullname)
            for client in self.user.clients:
                client.sendClose(code=4006, reason="Reconnect please.")


@cooldown(30)
class Lighter(LoultObject):
    NAME = "briquet"
    ICON = "lighter.gif"
    CIG_FX = DATA_PATH / Path("lighter.mp3")

    def use(self, obj_params):
        self.channel.broadcast(binary_payload=self._load_byte(self.CIG_FX))


@destructible
class MollyChute(LoultObject):
    NAME = "paras de MD"
    ICON = "paraMd.gif"

    class MDMAEffect(ExplicitTextEffect):
        NAME = "un paras"
        love_sentence = [
            "Attendez je vais kiffer le son là",
            "J'ai envie de vous faire un calin à tous",
            "Je peux t'embrasser %s?",
            "Vous êtes tous vraiment trop sympa en fait",
            "C'est tout doux quand je te caresse les cheveux %s",
            "Arrêtez de vous dire des trucs méchants moi je vous aime tous",
            "Franchement le monde est trop beau",
            "T'es vraiment trop sympa en fait %s",
            "C'est vraiment la plus belle soirée de ma vie",
            "t'as pas un chewing gum %s?",
            "attends faut que j'aille boire de l'eau"
        ]
        bad_trip_sentences = [
            "plus jamais je me défonce comme ça, c'est vraiment trop de la merde",
            "la vie est si nulle",
            "tellement la flemme de faire quoi que soit, marre de tout",
            "franchement ça sert à rien de sortir comme ça, dépenser son argent et se niquer la santé pour quelques heures de bonheur artificiel",
            "vraiment la descente je supporte plus, faut que j'arrête ces conneries",
            "je suis sûr que tu me détestes en fait %s",
            "j'ai trop chaud d'un coup",
            "mes parents doivent avoir honte de moi"
        ]
        TIMEOUT = 300
        # 100 last seconds are bad trippin'
        BAD_TRIP_TIME = 200

        def __init__(self, users_names):
            super().__init__()
            self.users = users_names
            self.start = datetime.now()

        def process(self, text: str):
            if random.randint(1, 3) == 1:
                if (datetime.now() - self.start).seconds < self.BAD_TRIP_TIME:
                    sentence = random.choice(self.love_sentence)
                else:
                    sentence = random.choice(self.bad_trip_sentences)

                if "%s" in sentence:
                    return sentence % random.choice(self.users)
                else:
                    return sentence
            else:
                return text

    def use(self, obj_params):
        efct = self.MDMAEffect([usr.poke_params.pokename for usr in self.channel.users.values()])
        self.user.state.add_effect(efct)
        self.channel.broadcast(type="notification",
                               msg="%s prend de la MD!" % self.user.poke_params.fullname)
        self.should_be_destroyed = True


@destructible
class CaptainHaddockPipe(LoultObject):
    NAME = "pipe du capitaine haddock"
    ICON = "haddockpipe.gif"

    def use(self, obj_params):
        self.user.state.add_effect(CaptainHaddockEffect())
        self.channel.broadcast(type="notification",
                               msg="%s est un marin d'eau douce!" % self.user.poke_params.fullname)
        self.should_be_destroyed = True


@destructible
@cooldown(10)
@targeted(mandatory=False)
class LaxativeBox(LoultObject):
    NAME = "Boite de laxatif industriel"
    ICON = "laxatif.gif"
    FX_DIR = DATA_PATH / Path("laxative")

    def __init__(self):
        super().__init__()
        self.remaining_use = 6

    @property
    def name(self):
        return f"{self.NAME} ({self.remaining_use})"

    def use(self, obj_params: List):
        if self.targeted_user is None:
            target = self.user
        else:
            target = self.targeted_user

        if target is self.user:
            msg = f"{self.user_fullname} prend un laxatif et fait kk paw tèw!"
        else:
            msg = f"{self.user_fullname} fait faire kk paw tèw à {target.poke_params.fullname}!"
            target.state.inventory.add(Poop(target.poke_params.fullname))
        fx_file = random.choice(list(self.FX_DIR.iterdir()))
        self.notify_channel(msg, binary_payload=self._load_byte(fx_file))
        self.remaining_use -= 1

        if self.remaining_use <= 0:
            self.should_be_destroyed = True


@destructible
@targeted(mandatory=False)
class Poop(LoultObject):
    ICON = "crotte.gif"
    FX_FOLDER = DATA_PATH / Path("throw_splat")

    def __init__(self, maker: str):
        super().__init__()
        self.maker = maker
        self.fx_file = random.choice(list(self.FX_FOLDER.iterdir()))

    @property
    def name(self):
        return f"kk de {self.maker}"

    def use(self, obj_params: List):
        if self.targeted_user is not None:
            target_dist = userlist_dist(self.channel, self.user.user_id, self.targeted_userid)
            if target_dist > 1:
                self.notify_serv(msg="Trop loin pour lancer du kk!")
                return

            msg = f"{self.user_fullname} lance le {self.name} sur {self.targeted_user.poke_params.fullname}!"
            self.notify_channel(msg=msg, binary_payload=self._load_byte(self.fx_file))
            self.targeted_user.disconnect_all_clients(code=4006, reason="Reconnect please")
        elif self.targeted_user is None or self.targeted_user is self.user:
            self.notify_channel(msg=f"{self.user.poke_params.fullname} s'étale le {self.name} sur le corps!")
        self.should_be_destroyed = True


@cooldown(30)
@targeted()
class Cacapulte(LoultObject):
    NAME = "cacapulte"
    ICON = "lance-pierre.gif"
    FX_FOLDER = DATA_PATH / Path("catapult_splat")

    def __init__(self):
        super().__init__()
        self.fx_file = random.choice(list(self.FX_FOLDER.iterdir()))

    def use(self, obj_params: List):
        poops = self.user_inventory.search_by_class(Poop)
        if not poops:
            self.notify_serv("Impossible de kk-pulter sans kk!")
            return
        poop = poops.pop()
        self.user_inventory.remove(poop)

        if self.targeted_user is self.user:
            self.notify_serv("Imposible de se tirer soi-même dessus!")
            return

        msg = f"{self.user_fullname} kk-pulte le {poop.name} sur {self.targeted_user.poke_params.fullname}!"
        self.notify_channel(msg=msg, binary_payload=self._load_byte(self.fx_file))
        self.targeted_user.disconnect_all_clients(code=4006, reason="Reconnect please")


@cooldown(60)
@targeted()
class EffectsStealer(LoultObject):
    NAME = "aspirateur d'effets"
    ICON = "aspirateur-2.gif"

    def use(self, obj_params: List):
        if self.targeted_user is self.user:
            self.notify_serv("Imposible d'aspirer ses propres effets!")
            return

        # stealing effects from the targeted user (their instance)
        for effect_type, effects in self.targeted_user.state.effects.items():
            for effect in effects:
                self.user.state.add_effect(effect)

        #  removing effects from the targeted user's effects list
        for effect_type in self.targeted_user.state.effects:
            self.targeted_user.state.effects[effect_type] = []

        self.notify_channel(
            f"{self.user_fullname} s'est accaparé les effets de {self.targeted_user.poke_params.fullname}!")


@destructible
class PandorasBox(LoultObject):
    NAME = "boite de pandore"
    ICON = "boite-pandore.gif"

    def use(self, obj_params: List):
        from ..effects import get_random_effect
        for user in self.channel.users.values():
            user.state.add_effect(get_random_effect())

        self.notify_channel(f"{self.user_fullname} a ouvert la boite de pandore !")
        self.should_be_destroyed = True


@cooldown(120)
class Transmutator(LoultObject):
    NAME = "transmutateur d'objets"
    ICON = "transmutateur.gif"

    FX_FILE = DATA_PATH / Path("transmutator.mp3")

    def use(self, obj_params: List):
        from ..objects import get_random_object
        other_objs = [obj for obj in self.user_inventory.objects
                      if obj is not self]
        if not other_objs:
            self.notify_serv("Pas d'objets à transmuter...")
            return

        rdm_obj: LoultObject = random.choice(other_objs)
        new_obj = get_random_object()
        self.user_inventory.remove(rdm_obj)
        self.user_inventory.add(new_obj)
        self.notify_serv(f"Objet {rdm_obj.name} changé en {new_obj.name}",
                         bin_payload=self._load_byte(self.FX_FILE))


@destructible
@cooldown(2)
@targeted(mandatory=True)
class SantasSack(LoultObject):
    NAME = "hotte du père noël"
    ICON = "cadeau.gif"

    def __init__(self, presents: Optional[int] = None):
        super().__init__()
        if presents is None:
            self.present_count = random.randint(3, 8)
        else:
            self.present_count = presents
        self.last_recipient = None

    def use(self, obj_params: List):
        if self.targeted_user is self.user:
            self.notify_serv("On offre les cadeau aux autres, pas à soit-même, espèce d'égoïste de merde!")
            return

        if len(self.targeted_user.state.inventory.objects) >= 15:
            self.notify_serv("L'utilisateur cible a déjà trop d'objets!")
            return

        if self.targeted_user is self.last_recipient:
            self.notify_serv("Pas toujours le même espèce de père noël de carnaval!")
            return

        from ..objects import get_random_object
        obj = get_random_object()
        self.targeted_user.state.inventory.add(obj)
        self.notify_channel(
            f"{self.user_fullname} a offert un beau {obj.name} à {self.targeted_user.poke_params.fullname}!")
        self.present_count -= 1
        self.last_recipient = self.targeted_user
        if self.present_count <= 0:
            self.should_be_destroyed = True
