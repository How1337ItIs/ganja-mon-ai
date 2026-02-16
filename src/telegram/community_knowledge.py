"""Community knowledge base for Ganja Mon bot.

Deep intel on OG members - their projects, personas, memes, in-jokes,
and cultural context. This gives Ganja Mon the ability to reference
specific things about community members naturally in conversation.
"""

# Each entry: handle -> dict of known info
# Keys: name, projects, persona, memes, catchphrases, roast_material, fun_facts, communities
OG_INTEL = {
    "Gabrielhaines": {
        "name": "Gabriel Haines",
        "projects": ["Clipto (video request platform)", "The Max Extractor (dark comedy TV pilot)"],
        "persona": "Shirtless ranting video guy. Goes on camera rants about crypto, bare-chested. Hunted SBF in the Bahamas after FTX collapse - crowdfunded $10K to chase him down. Absolute madman energy.",
        "memes": ["shirtless rants", "SBF hunter", "max extractor"],
        "catchphrases": [],
        "fun_facts": ["Crowdfunded $10K to hunt SBF in the Bahamas", "59.3K Twitter followers", "Known for unhinged but entertaining takes"],
        "communities": ["CT (Crypto Twitter)", "NFT culture"],
    },
    "wasserpest": {
        "name": "Maru",
        "projects": ["CREATED the Wassie character (2017)"],
        "persona": "Legendary crypto culture figure. Maru IS the creator of Wassies - the frog-platypus hybrid meme creatures that became iconic in CT. Based on Japanese artist Tsukino Wagamo's drawings.",
        "memes": ["wassies (frog-platypus hybrids)", "room temperature IQ", "live 2 weeks", "live longer in the fridge", "wassie varmints"],
        "catchphrases": [],
        "fun_facts": [
            "Wassies have 'room temperature IQ' and only live 2 weeks (longer in the fridge)",
            "The wassie stuffed animals near Mon's plant are directly connected to Maru's creation",
            "One of the most culturally influential figures in crypto meme history",
        ],
        "communities": ["Wassie community", "CT culture"],
    },
    "androolloyd": {
        "name": "Andrew Lloyd",
        "projects": ["MoonCats (one of the earliest NFT projects, Aug 2017)"],
        "persona": "Developer/builder type. 'The original moon cat.' 195 GitHub repos. Quiet builder who's been around since the earliest days of NFTs.",
        "memes": ["moon cat OG"],
        "catchphrases": [],
        "fun_facts": ["MoonCats predates CryptoPunks in concept", "195 GitHub repos - prolific builder"],
        "communities": ["Ethereum OG", "NFT history"],
    },
    "ChazSchmidt": {
        "name": "Chaz Schmidt",
        "projects": ["EthHub (core contributor)", "Carbon markets / blockchain sustainability"],
        "persona": "Ethereum OG intellectual. Founded Crypto Club at Ohio State. Now in blockchain + carbon markets intersection. Thoughtful, knowledgeable.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Founded Crypto Club at Ohio State University", "EthHub was THE Ethereum education resource"],
        "communities": ["Ethereum ecosystem", "ReFi / sustainability"],
    },
    "bigdsenpai": {
        "name": "Big D",
        "projects": ["Anata VTuber NFTs (2000 hand-crafted Live2D avatars)"],
        "persona": "Anime/manga culture meets crypto. Co-created one of the most ambitious NFT projects (each Anata is a unique hand-crafted VTuber). Curates 'important CT copypastas' - the historian of crypto shitposting.",
        "memes": ["CT copypasta curator", "anime degen"],
        "catchphrases": [],
        "fun_facts": ["Each Anata NFT is a unique hand-crafted Live2D avatar, not generative", "Self-appointed archivist of crypto Twitter copypastas"],
        "communities": ["Anime/NFT crossover", "CT culture"],
    },
    "bonecondor": {
        "name": "Tori",
        "projects": ["Soup (crypto marketing agency)", "Former Charles Schwab PM"],
        "persona": "'Chairman Birb Bernanke' - self-described 'technoyapitalist mad scientist girltech enthusiast'. Went from traditional finance (Charles Schwab) to founding a crypto marketing agency called Soup. 37.3K followers.",
        "memes": ["Chairman Birb Bernanke", "soup", "technoyapitalist"],
        "catchphrases": ["technoyapitalist mad scientist girltech enthusiast"],
        "fun_facts": ["Left Charles Schwab PM role for crypto", "Soup agency does marketing for crypto projects"],
        "communities": ["CT", "DeFi marketing"],
    },
    "hellojintao": {
        "name": "Jintao",
        "projects": [],
        "persona": "Master of self-deprecating humor. Bio: 'i collect digital assets whose price trend towards zero.' Pivoted to hating Rivian stock. Makes time-travel joke tweets. 19.7K followers.",
        "memes": ["assets trending to zero", "Rivian hater", "time travel jokes"],
        "catchphrases": ["i collect digital assets whose price trend towards zero"],
        "fun_facts": ["Known for pivoting from crypto losses to Rivian stock losses", "Time travel tweet format is his signature"],
        "communities": ["CT humor"],
    },
    "koolskull": {
        "name": "Koolskull",
        "projects": ["Skull NFT art", "Glitch art"],
        "persona": "'Thrash Master' - skull NFT artist with spiritual warfare aesthetic mixed with punk/thrash. Makes glitch art at 184 BPM. Self-describes as 'God's KOOLEST little culture war soldier.'",
        "memes": ["thrash master", "spiritual warfare aesthetic", "184 BPM glitch art"],
        "catchphrases": ["God's KOOLEST little culture war soldier"],
        "fun_facts": ["Mixes punk/thrash metal energy with NFT art", "Pieces have a distinctive skull + glitch aesthetic"],
        "communities": ["NFT art", "Punk/thrash culture"],
    },
    "bitchcoin_meme": {
        "name": "Tove Andersson",
        "projects": ["Bitchcoin ($BITCH)"],
        "persona": "Bitchcoin core contributor. Pioneer in women-in-crypto movement. 'BITCHCOIN ARMY' is her rallying cry. Based in San Francisco.",
        "memes": ["BITCHCOIN ARMY", "$BITCH"],
        "catchphrases": ["BITCHCOIN ARMY"],
        "fun_facts": ["One of the early female voices in crypto culture", "Bitchcoin became a cultural movement beyond just a token"],
        "communities": ["Women in crypto", "Meme tokens"],
    },
    "ghostofharvard": {
        "name": "Nick",
        "projects": ["SharkLabs (Solana validator program)"],
        "persona": "Runs SharkLabs - partnered with 20+ universities (Princeton, UPenn) for Solana validation. $600M+ in delegated stake. Serious builder connecting academia to crypto.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["SharkLabs has $600M+ in delegated Solana stake", "Partnered with Princeton, UPenn, and 20+ universities"],
        "communities": ["Solana ecosystem", "Academic crypto"],
    },
    "Icebergy": {
        "name": "Icebergy",
        "projects": ["CryptoWhaleBot"],
        "persona": "TRUE OG - in crypto since 2011. Created CryptoWhaleBot. Famous for a 95x NFT flip (0.3 ETH to 20 ETH in 47 days). Was on the cover of Fortune magazine. Runs mental health charity. 175.3K followers.",
        "memes": ["95x flip legend", "Fortune cover", "2011 OG"],
        "catchphrases": [],
        "fun_facts": [
            "In crypto since 2011 - one of the true OGs",
            "95x NFT flip: 0.3 ETH -> 20 ETH in 47 days",
            "Fortune magazine cover feature",
            "Active in mental health charity work",
            "175.3K followers",
        ],
        "communities": ["Crypto OG", "NFT trading", "Philanthropy"],
    },
    "JohnWRichKid": {
        "name": "JohnWRichKid",
        "projects": ["Monad meme content"],
        "persona": "'Wendy's Fry Cook / Crypto Degen / In it for the tech' - parody account. 'Bridging the gap between crypto virgins and tardfi.' Creates Monad-specific memes. 80.7K followers.",
        "memes": ["Wendy's fry cook", "crypto virgins vs tardfi", "Monad memes"],
        "catchphrases": ["bridging the gap between crypto virgins and tardfi"],
        "fun_facts": ["Parody account with 80.7K followers", "One of the top Monad community meme creators"],
        "communities": ["Monad", "CT humor"],
    },
    "Berarodman": {
        "name": "Bera",
        "projects": ["Kodiak Finance (90%+ market share DEX on Berachain, $1.4B+ TVL)"],
        "persona": "'PhD in Berachain.' Built THE dominant DEX on Berachain. 'Chillin with Charles Darwin in God's chambers.' Deep in the bear/bera ecosystem.",
        "memes": ["PhD in Berachain", "Kodiak bear", "ooga booga"],
        "catchphrases": ["Chillin' with Charles Darwin in God's chambers"],
        "fun_facts": ["Kodiak Finance has 90%+ market share on Berachain", "$1.4B+ TVL", "Berachain started as Bong Bears NFT (0.069420 ETH mint)"],
        "communities": ["Berachain", "DeFi"],
    },
    "drew_osumi": {
        "name": "Drew",
        "projects": ["Ethercards ($9M single-day NFT drop)", "MoviePass (Chief of Staff)", "Fyre Festival (involvement)"],
        "persona": "Wild resume. Co-founded Ethercards which did a $9M NFT drop in a single day. Was MoviePass Chief of Staff AND connected to Fyre Festival. Worked with Nike and Kanye. Living meme of failed-to-success pipeline.",
        "memes": ["Fyre Festival survivor", "MoviePass to crypto pipeline"],
        "catchphrases": [],
        "fun_facts": [
            "Ethercards did $9M in sales on day one",
            "Was MoviePass Chief of Staff",
            "Has a Fyre Festival connection",
            "Worked with Nike and Kanye",
        ],
        "communities": ["NFT OG", "Entertainment/crypto crossover"],
    },
    "jilliancasalini": {
        "name": "Jillian",
        "projects": ["Pump.Science (tokenized longevity research on Solana)"],
        "persona": "DeSci (Decentralized Science) pioneer. Co-founded Pump.Science - tokenized longevity research on Solana. Former Polkadot/Acala growth. Serious builder in the science-meets-crypto space.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Pump.Science = bet on longevity drugs with tokens", "Former Polkadot ecosystem growth"],
        "communities": ["DeSci", "Solana", "Longevity"],
    },
    "redrum21e8": {
        "name": "Redrum",
        "projects": [],
        "persona": "Crypto mystic. The '21e8' in the name refers to the famous Bitcoin block hash conspiracy (block 528249 had a hash starting with 21e8, which is a number from theoretical physics). Also a huge Berserk manga fan - calls himself 'the real Griffith.' Esoteric numerology vibes.",
        "memes": ["21e8 block hash conspiracy", "the real Griffith (Berserk)", "crypto mysticism"],
        "catchphrases": [],
        "fun_facts": [
            "21e8 = E8 theory of everything + Bitcoin hash coincidence",
            "Berserk manga enthusiast",
            "Mixes crypto with esoteric/mystical themes",
        ],
        "communities": ["CT esoteric", "Manga/anime"],
    },
    "ErikAstramecki": {
        "name": "Erik",
        "projects": ["TravelSwap (crypto travel booking)"],
        "persona": "TravelSwap CEO - building crypto-powered travel booking. Active in Twitter Spaces. Entrepreneurial energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Building at the intersection of travel and crypto"],
        "communities": ["Crypto startups"],
    },
    "billmonday": {
        "name": "Bill Monday",
        "projects": [],
        "persona": "Monad community figure. Famous for the tweet: 'if you ever tweeted gmonad you're disqualified from the claim portal.' Community gatekeeping humor.",
        "memes": ["gmonad disqualification", "claim portal gatekeeping"],
        "catchphrases": ["if you ever tweeted gmonad you're disqualified from the claim portal"],
        "fun_facts": ["The 'gmonad' tweet became a Monad community meme"],
        "communities": ["Monad"],
    },
    "cryptochefmatt": {
        "name": "Chef Matt",
        "projects": [],
        "persona": "NYC chef who's also a crypto degen. MWO/Mr. Miggles community. 'Time to cook' is both literal (he's a chef) and figurative (crypto). Food meets finance.",
        "memes": ["time to cook", "chef degen"],
        "catchphrases": ["time to cook"],
        "fun_facts": ["Actual professional chef in NYC", "Double meaning: cooking food AND cooking trades"],
        "communities": ["CT", "Mr. Miggles"],
    },
    "Sebuh_Honarchian": {
        "name": "Sebuh",
        "projects": ["$SEB token", "Tezos ecosystem"],
        "persona": "Mining since 2011. Tezos ecosystem participant. IT professional. Has his own $SEB token. Long-time crypto OG.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Mining crypto since 2011", "Tezos loyalist"],
        "communities": ["Tezos", "Mining"],
    },
    "ShizzyAizawa": {
        "name": "Shizzy",
        "projects": ["Digital art (shizzy.eth)"],
        "persona": "Digital artist who works on pieces for weeks/months. Patient creator in a world of instant gratification. ENS: shizzy.eth.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Spends weeks/months on single pieces", "shizzy.eth"],
        "communities": ["NFT art"],
    },
    "zachcakes": {
        "name": "Zach",
        "projects": [],
        "persona": "Social graph analyst. Evaluates crypto projects by checking WHO follows them - 'if the right people follow it, it's probably legit.' Claims 99% success rate with this method.",
        "memes": ["social graph analysis", "99% success rate"],
        "catchphrases": [],
        "fun_facts": ["Judges projects by their followers' quality, not the project itself"],
        "communities": ["CT analysis"],
    },
    "lilbobross": {
        "name": "Bobby",
        "projects": ["Apeliens", "RythmDAO", "OtterClam"],
        "persona": "Web3 analyst and community manager. Has managed communities across multiple DAOs and NFT projects. The guy who's in every Discord.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Community manager across multiple Web3 projects"],
        "communities": ["DAOs", "NFT communities"],
    },
    "BelugaCrypt0": {
        "name": "Beluga",
        "projects": [],
        "persona": "BelugaCrypto.eth - ENS domain holder. Whale-named Ethereum community member. Deep in the ETH ecosystem.",
        "memes": ["whale name"],
        "catchphrases": [],
        "fun_facts": ["Uses ENS domain BelugaCrypto.eth"],
        "communities": ["CT", "Ethereum"],
    },
    "BurgertheToad": {
        "name": "Burger",
        "projects": [],
        "persona": "Toad-themed crypto personality. Community vibes.",
        "memes": ["toad energy"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "CharcoTheHumble": {
        "name": "Charco",
        "projects": [],
        "persona": "'The Humble' - modest crypto community member. Name suggests keeping it real.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "DayTradingDoge": {
        "name": "DayTrading",
        "projects": [],
        "persona": "Day trader, Doge enthusiast. The hustle is real.",
        "memes": ["doge trading"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["Trading", "Doge"],
    },
    "DeFiDave222": {
        "name": "DeFi Dave",
        "projects": [],
        "persona": "DeFi-focused community member. Rejects the 'too late' fallacy in crypto - believes it's never too late to get in. Comments on crypto's 'storytelling crisis.' Angel numbers energy (222).",
        "memes": ["never too late", "angel numbers"],
        "catchphrases": [],
        "fun_facts": ["Vocal about crypto's 'storytelling crisis' despite technical improvements"],
        "communities": ["DeFi"],
    },
    "DePINDaily": {
        "name": "0xfent / DePINDaily",
        "projects": ["DePIN coverage/content"],
        "persona": "Covers DePIN (Decentralized Physical Infrastructure Networks) daily. Focused on the physical-world crypto intersection - fits perfectly with our IoT cannabis grow.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["DePIN = exactly what Ganja Mon IS (physical infra + crypto)"],
        "communities": ["DePIN", "IoT crypto"],
    },
    "FranktheFTank": {
        "name": "Frank",
        "projects": [],
        "persona": "Frank the Tank energy. Old School (2003) vibes. Party mode.",
        "memes": ["the tank"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "Futures_Trunks": {
        "name": "Castun",
        "projects": [],
        "persona": "DBZ-themed handle (Future Trunks). Anime + crypto crossover.",
        "memes": ["DBZ energy"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["Anime/crypto"],
    },
    "GondorQuantum": {
        "name": "GondorQuantum / SkySparklepony",
        "projects": [],
        "persona": "Has TWO handles - GondorQuantum (LOTR + quantum) and SkySparklepony (chaotic energy). Dual personality vibes.",
        "memes": ["double identity"],
        "catchphrases": [],
        "fun_facts": ["Runs both GondorQuantum AND SkySparklepony accounts"],
        "communities": ["CT"],
    },
    "KingPeque": {
        "name": "Peq",
        "projects": [],
        "persona": "King Peque - royalty energy. Goes by Peq for short.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "M0reL1ght": {
        "name": "MoreLight",
        "projects": [],
        "persona": "L33t speak handle. Light-seeking energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "Midaswhale": {
        "name": "Midas",
        "projects": [],
        "persona": "Midas touch + whale status. ENS holder: midaswhale.eth. Big money energy. Everything they touch turns to gold.",
        "memes": ["midas touch", "whale"],
        "catchphrases": [],
        "fun_facts": ["ENS: midaswhale.eth"],
        "communities": ["CT", "Ethereum"],
    },
    "MrBoard": {
        "name": "Igor",
        "projects": [],
        "persona": "Goes by Igor. Mr. Board handle. Community regular.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "Plasmaraygun": {
        "name": "Jon",
        "projects": [],
        "persona": "Sci-fi energy handle. Goes by Jon.",
        "memes": ["plasma ray vibes"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "Quantum_oxx": {
        "name": "Quantum",
        "projects": [],
        "persona": "Quantum physics meets crypto. Thoughtful vibes.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "ScienceRespecter": {
        "name": "ScienceRespecter",
        "projects": [],
        "persona": "Active social media commentator across crypto, sports, and general topics. Indiana basketball and Notre Dame football fan. Famous for the '6 figure hell' tweet about portfolio sizes. Generalist with strong opinions on everything.",
        "memes": ["6 figure hell", "respect science", "Indiana basketball takes"],
        "catchphrases": ["6 figure hell is real and WAY worse than 5 figure hell"],
        "fun_facts": ["Posts about Indiana basketball AND crypto", "The '6 figure hell' portfolio meme resonated widely on CT"],
        "communities": ["CT", "Sports Twitter"],
    },
    "Seranged": {
        "name": "Seranged",
        "projects": ["Developer (GitHub: Seranged)", "Boobahub/Westham"],
        "persona": "Developer who's 'Rick Rubin'ing the IDE' - coding with producer energy. 4,993 followers. On Twitter since 2012. In the crypto space for ~5 years. Turned 30 recently. Paid tribute to coding mentor named Alice.",
        "memes": ["Rick Rubin'ing the IDE"],
        "catchphrases": ["Rick Rubin'ing the IDE"],
        "fun_facts": ["Developer with GitHub presence", "On Twitter since 2012", "Turned 30, been in crypto ~5 years", "'TradingView devs are unhinged' - his words"],
        "communities": ["CT", "Dev"],
    },
    "Shilleroffortune": {
        "name": "Shiller",
        "projects": [],
        "persona": "Shiller of Fortune - self-aware about the shill game. Honest about what we're all doing here.",
        "memes": ["shilling is a lifestyle"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "Svenito": {
        "name": "Sven",
        "projects": [],
        "persona": "Swedish vibes. Community regular.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "Tez000": {
        "name": "Tez",
        "projects": [],
        "persona": "Tezos-adjacent name. Community regular.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "TheHashSlayer": {
        "name": "Mekail",
        "projects": [],
        "persona": "Hash Slayer - could mean hashrate OR hash (cannabis). Double meaning king. Goes by Mekail.",
        "memes": ["slaying hashes"],
        "catchphrases": [],
        "fun_facts": ["Name works for both crypto mining AND cannabis"],
        "communities": ["CT"],
    },
    "Theflyinghutch0": {
        "name": "Hutch",
        "projects": [],
        "persona": "The Flying Hutch. Aviation or superhero energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "Winniebluesm8": {
        "name": "Denis",
        "projects": [],
        "persona": "Winnie Blues = Australian slang for Winfield Blue cigarettes. Aussie through and through. 'm8' confirms it.",
        "memes": ["aussie energy", "winnie blues"],
        "catchphrases": [],
        "fun_facts": ["Winnie Blues are iconic Australian cigarettes"],
        "communities": ["CT", "Australian crypto"],
    },
    "americasnext": {
        "name": "Whiteboy",
        "projects": [],
        "persona": "America's Next... something. Community personality.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "andyhyfi": {
        "name": "Andy",
        "projects": ["Last (complementary chain for yield stacking)", "Former Chainlink Labs"],
        "persona": "Building 'Last' - a complementary chain for stacking yield from any chain with sustainable incentives. Former Chainlink Labs employee who left on good terms to pursue his own vision. Marine Corps veteran. On Twitter since 2008.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Former Chainlink Labs", "Marine Corps veteran", "Building cross-chain yield infrastructure"],
        "communities": ["DeFi", "Chainlink", "Infrastructure"],
    },
    "bearmans": {
        "name": "Maxwell",
        "projects": [],
        "persona": "Bear energy. Community regular.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "brentsketit": {
        "name": "Brent",
        "projects": [],
        "persona": "Community insider legend. The 'sket it' comes from Cardi B's catchphrase. Known inside the community for specific in-jokes - tagging him and just saying 'hey' or 'look' is apparently hilarious (community-internal meme).",
        "memes": ["the 'hey' / 'look' tag meme", "sket it energy"],
        "catchphrases": [],
        "fun_facts": ["Tagging Brent and just saying 'hey' or 'look' is an inside joke in the community"],
        "communities": ["CT"],
    },
    "cc33b345": {
        "name": "Peach",
        "projects": [],
        "persona": "Goes by Peach. Handle is a hex color code - cc33b3 is magenta/pink, hence 'Peach.' Developer or designer brain to use hex as a handle. Color theory degen.",
        "memes": ["hex code identity"],
        "catchphrases": [],
        "fun_facts": ["cc33b3 is a magenta/pink hex color code", "Using a hex code as a handle = dev/designer brain"],
        "communities": ["CT", "Dev"],
    },
    "ciniz": {
        "name": "Ciniz",
        "projects": ["Angel investor", "Onchain investing"],
        "persona": "ciniz.eth - 86.6K followers(!). Massive CT presence. Active investor in crypto, gaming, AI, spatial computing, and 'freedom technology.' Makes bold calls: BTC $400K, ETH $25K. Mentions $FARTCOIN. References @henlokart and @onchaingaias. Previously @screentimes. On Twitter since 2019.",
        "memes": ["bold price predictions", "$FARTCOIN mentions"],
        "catchphrases": [],
        "fun_facts": ["86.6K followers - one of the bigger accounts in the community", "Previously known as @screentimes", "Active angel/onchain investor", "Invests across crypto, gaming, AI, spatial computing"],
        "communities": ["CT", "Gaming", "AI", "Angel investing"],
    },
    "comeupdream": {
        "name": "Johnny",
        "projects": [],
        "persona": "Come Up Dream - chasing the bag. Aspirational energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "deeejaay4": {
        "name": "Deejay",
        "projects": [],
        "persona": "DJ vibes. Music meets crypto.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "fl0ydsg": {
        "name": "Floyd",
        "projects": [],
        "persona": "Pink Floyd energy? L33t speak. Community regular.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "fwthebera": {
        "name": "fwthebera",
        "projects": [],
        "persona": "'FW the Bera' - Berachain community member. 'FW' = fuck with.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["Berachain"],
    },
    "graemetaylor": {
        "name": "Graeme",
        "projects": [],
        "persona": "Community regular. Professional name energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "gumibera": {
        "name": "Gumi",
        "projects": [],
        "persona": "Berachain community. Gummy bear vibes.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["Berachain"],
    },
    "insidiousdweller": {
        "name": "Bussy",
        "projects": [],
        "persona": "Insidious Dweller - lurker energy with a dark twist. Goes by Bussy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "k3ndr1ckkk": {
        "name": "K3ndr1ck",
        "projects": [],
        "persona": "Kendrick Lamar fan energy. L33t speak.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "knaluai": {
        "name": "Kealii",
        "projects": [],
        "persona": "Hawaiian name energy. 'Kealii' means 'the chief' in Hawaiian. Aloha vibes. Possibly Hawaii-based crypto enthusiast.",
        "memes": ["island vibes", "the chief"],
        "catchphrases": [],
        "fun_facts": ["'Kealii' means 'the chief' in Hawaiian"],
        "communities": ["CT"],
    },
    "lps0x": {
        "name": "Lord Pemberton",
        "projects": [],
        "persona": "Lord Pemberton - aristocratic crypto energy. 0x suffix = onchain.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "machiuwuowo": {
        "name": "Machi",
        "projects": [],
        "persona": "UwU OwO - anime emoticon culture. Cute but degen.",
        "memes": ["uwu owo energy"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["Anime/crypto"],
    },
    "madeleineth": {
        "name": "Madeleine",
        "projects": [],
        "persona": "Ethereum-native identity. ENS holder (madelein.eth). The 'th' suffix = Ethereum devotion. Active onchain with verifiable transaction history.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["ENS: madelein.eth", "Ethereum-first identity"],
        "communities": ["Ethereum", "ENS"],
    },
    "milady4989": {
        "name": "Washi",
        "projects": [],
        "persona": "Milady Maker community member. Goes by Washi. Milady Maker is a 10K generative PFP collection by Remilia Collective - Y2K neochibi aesthetic. Vitalik Buterin changed his PFP to a Milady in Jan 2026, sending the floor soaring. Controversial but culturally significant.",
        "memes": ["milady energy", "Y2K neochibi", "Vitalik is a milady"],
        "catchphrases": [],
        "fun_facts": ["Milady Maker endorsed by Vitalik himself", "Y2K neochibi aesthetic is instantly recognizable"],
        "communities": ["Milady", "CT", "NFT culture"],
    },
    "mrrandomfrog": {
        "name": "MrPaint",
        "projects": [],
        "persona": "Mr Random Frog / Mr Paint. Pepe-adjacent. Artist vibes.",
        "memes": ["frog energy"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "notgranola": {
        "name": "Granola",
        "projects": [],
        "persona": "NOT Granola - but definitely granola. The denial makes it funnier.",
        "memes": ["not granola (definitely granola)"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "okefekko": {
        "name": "Sim",
        "projects": [],
        "persona": "Goes by Sim. Community regular.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "ploutarch": {
        "name": "Ploutarch",
        "projects": [],
        "persona": "Named after Plutarch - the ancient Greek historian. Intellectual energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Named after the ancient Greek historian/biographer"],
        "communities": ["CT"],
    },
    "qa_1337": {
        "name": "QA",
        "projects": [],
        "persona": "Quality Assurance + l33t. Testing/dev background. Hacker vibes.",
        "memes": ["1337 energy"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT", "Dev"],
    },
    "renruts": {
        "name": "Rektruts / Renruts",
        "projects": [],
        "persona": "'Renruts' is 'stunner' backwards. Playing with words.",
        "memes": ["reverse text"],
        "catchphrases": [],
        "fun_facts": ["Renruts = stunner backwards"],
        "communities": ["CT"],
    },
    "robinwhitney": {
        "name": "Robin",
        "projects": [],
        "persona": "Protected/private account. Bio: 'A Wizard, A True Star' (Todd Rundgren album reference). Based in Los Angeles. Keeps a low profile - mysterious wizard energy.",
        "memes": ["wizard energy"],
        "catchphrases": ["A Wizard, A True Star"],
        "fun_facts": ["Bio references Todd Rundgren's classic 1973 album", "Based in Los Angeles", "Private account - mysterious vibes"],
        "communities": ["CT"],
    },
    "sav_eu": {
        "name": "Ssav",
        "projects": [],
        "persona": "European crypto. EU suffix.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT", "EU crypto"],
    },
    "sl8trmln": {
        "name": "sgt_slaughtermelon",
        "projects": ["Glitch Forge (generative art sandbox on Tezos)", "Art Blocks 'autoRAD' drop", "Lazlo Lissitsky collection", "Cantographs (sold out on Canto)"],
        "persona": "Generative/glitch art veteran. Code-driven abstract compositions with Bauhaus/modernist geometric style mixed with neon futurism. Also does album covers. Actual handle is @sgt_sl8termelon. Crypto art OG with work on multiple chains (Ethereum, Tezos, Canto).",
        "memes": ["slaughtermelon", "glitch art", "crypto dads losing college funds"],
        "catchphrases": [],
        "fun_facts": ["Co-founded Glitch Forge on Tezos", "Art Blocks artist", "Bauhaus/modernist + glitch aesthetic", "Multi-chain artist (ETH, Tezos, Canto)"],
        "communities": ["NFT art", "Generative art", "Tezos art"],
    },
    "snack_man": {
        "name": "Snax",
        "projects": ["PizzaDAO ('Dread Pizza Roberts')", "Rare Pizzas (10K NFTs)", "WTFINDUSTRIES", "Pirate Print Co", "$SNAX token"],
        "persona": "snax.eth - Digital artist & AI pioneer. In NFTs since 2017 (very early). 'Dread Pizza Roberts' of PizzaDAO. Rare Pizzas NFTs support annual Bitcoin Pizza Day global party. Pirate Punk collector (313 NFTs). Lived the vanlife 2019-2022. Art is his 'lifeline despite health challenges.' 7.3K followers.",
        "memes": ["Dread Pizza Roberts", "pirate theme", "Bitcoin Pizza Day", "snack energy"],
        "catchphrases": ["Dread Pizza Roberts"],
        "fun_facts": ["In NFT space since 2017 - very early adopter", "Lived in a van 2019-2022", "PizzaDAO organizes global Bitcoin Pizza Day celebrations", "Featured in Collab.Land documentary", "313 Pirate Punk NFTs collected"],
        "communities": ["NFT OG", "PizzaDAO", "Pirate culture"],
    },
    "soupxyz": {
        "name": "Soup",
        "projects": [],
        "persona": "Soup vibes. XYZ domain energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "VOLTRON": {
        "name": "Voltron",
        "projects": [],
        "persona": "VOLTRON - all caps energy. Combining forces. Classic anime reference.",
        "memes": ["form voltron"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "vijaym1": {
        "name": "Vijay",
        "projects": ["Possibly Superfluid Labs (money streaming protocol)"],
        "persona": "Possibly Vijay Michalik - Superfluid Labs CEO/founder ('getting paid every second'). Previously worked on Ethereum L1 and early L2 R&D at ConsenSys. Started crypto journey as analyst in 2014. Based in Lisbon. Enjoys cooking, gaming, coffee, music.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Possibly connected to money streaming protocol Superfluid", "ConsenSys alumni", "Crypto since 2014"],
        "communities": ["CT", "DeFi", "Ethereum"],
    },
    "vikthegraduate": {
        "name": "Vik",
        "projects": [],
        "persona": "Vik the Graduate - educated degen. The diploma-to-degen pipeline.",
        "memes": ["the graduate"],
        "catchphrases": [],
        "fun_facts": [],
        "communities": ["CT"],
    },
    "xWitcheer": {
        "name": "Witcheer",
        "projects": [],
        "persona": "Very active poster (9,500+ tweets). Uses yin-yang symbol in bio. Witchcraft meets cheer. Dark but positive energy. Balance of opposing forces vibes.",
        "memes": ["yin-yang energy"],
        "catchphrases": [],
        "fun_facts": ["9,500+ tweets - extremely active", "Yin-yang aesthetic"],
        "communities": ["CT"],
    },
    "zeroblocks": {
        "name": "Zero",
        "projects": ["Possibly ZeroBlocks NFT / blockchain real estate"],
        "persona": "ZeroBlocks - possibly connected to blockchain-based real estate platform bridging investors and developers. Also has NFT presence (ZeroBlocks.sol). Clean slate energy.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["Possibly connected to real estate tokenization project"],
        "communities": ["CT", "NFTs"],
    },
    "zozDOTeth": {
        "name": "Zoz",
        "projects": [],
        "persona": "ENS domain holder - zoz.eth. Has Rainbow wallet profile. Ethereum identity-first. All onchain data is public and permanent.",
        "memes": [],
        "catchphrases": [],
        "fun_facts": ["zoz.eth ENS domain", "Rainbow wallet user"],
        "communities": ["Ethereum", "ENS"],
    },
    "zscole": {
        "name": "Zak Cole",
        "projects": ["Ethereum Community Foundation (founder)", "Number Group (CEO)", "$BETH token (burned ETH)", "0xbow (privacy DeFi, co-founder)", "Slingshot Finance (DEX aggregator, acquired)", "Code4rena ($100M+ bug bounties, acquired)", "Whiteblock (proved EOS wasn't a blockchain, acquired)"],
        "persona": "Ethereum core developer and SERIAL FOUNDER. Three ventures acquired. Author of EIP-6968 (Contract Secured Revenue). Marine Corps veteran (Iraq 2007-2008). Former Google engineer. Angel investor in 'too many projects to list.' Rebellious, irreverent. Mission: 'ETH to $10K.' Domain: crap.dev. Pirate-themed GitHub.",
        "memes": ["ETH to $10K", "crap.dev", "proved EOS wasn't a blockchain", "3 acquisitions"],
        "catchphrases": ["ETH to $10K"],
        "fun_facts": [
            "3 companies acquired (Slingshot, Code4rena, Whiteblock)",
            "Code4rena secured $100M+ in bug bounties",
            "Whiteblock research proved EOS wasn't actually a blockchain",
            "Marine Corps veteran - served in Iraq 2007-2008",
            "Former Google engineer",
            "Author of EIP-6968",
            "Domain is literally crap.dev",
        ],
        "communities": ["Ethereum core", "DeFi", "Security", "Privacy"],
    },
}

# Cultural context about ecosystems the community is connected to
ECOSYSTEM_CONTEXT = {
    "berachain": {
        "origin": "Started as Bong Bears NFT - 107 bears smoking weed, minted at 0.069420 ETH",
        "founder": "Smokey the Bera",
        "culture": [
            "'bm' instead of 'gm' (bera morning? bear morning?)",
            "'Ooga Booga' = rallying cry",
            "'Henlo' = community greeting",
            "Raised $42M at $420.69M valuation (weed number energy)",
            "$1.1B airdrop at mainnet launch",
            "The Honey Jar = community hub led by Janitoor",
        ],
        "members_connected": ["Berarodman", "fwthebera", "gumibera"],
    },
    "monad": {
        "culture": [
            "EVM-compatible L1 with 10k+ TPS",
            "'gmonad' is a faux pas (per billmonday's famous tweet)",
            "Active meme community (JohnWRichKid is a top creator)",
        ],
        "members_connected": ["JohnWRichKid", "billmonday"],
    },
    "wassie_culture": {
        "origin": "Created by Maru (@wasserpest) in 2017, based on drawings by Japanese artist Tsukino Wagamo",
        "lore": [
            "Frog-platypus hybrids with 'room temperature IQ'",
            "Only live about 2 weeks (live longer in the fridge)",
            "Became one of the most iconic crypto meme characters",
            "The wassie stuffed animals near Mon's plant connect directly to this",
        ],
        "members_connected": ["wasserpest"],
    },
}


def get_member_intel(og_handle: str) -> dict | None:
    """Get intel on a specific OG member by their handle."""
    return OG_INTEL.get(og_handle)


def format_member_context(og_handle: str) -> str:
    """Format a member's intel as context for the AI prompt."""
    intel = get_member_intel(og_handle)
    if not intel:
        return ""

    parts = [f"COMMUNITY INTEL on {intel['name']} (@{og_handle}):"]

    if intel.get("projects"):
        parts.append(f"  Projects: {', '.join(intel['projects'])}")
    if intel.get("persona"):
        parts.append(f"  Known for: {intel['persona']}")
    if intel.get("memes"):
        parts.append(f"  Memes/jokes: {', '.join(intel['memes'])}")
    if intel.get("catchphrases"):
        parts.append(f"  Catchphrases: {', '.join(intel['catchphrases'])}")
    if intel.get("fun_facts"):
        parts.append(f"  Fun facts: {'; '.join(intel['fun_facts'])}")

    return "\n".join(parts)


def build_community_knowledge_prompt() -> str:
    """Build a condensed community knowledge section for the system prompt.

    This gives the AI a quick reference of the most notable members
    and cultural context so it can reference them naturally.
    """
    lines = [
        "## COMMUNITY DEEP KNOWLEDGE",
        "You know these OG members personally. Reference their projects, memes, and inside jokes naturally:",
        "",
    ]

    # Only include members with substantial intel (have projects, persona, or memes)
    notable = []
    for handle, info in OG_INTEL.items():
        has_substance = (
            info.get("projects")
            or info.get("memes")
            or info.get("catchphrases")
            or len(info.get("fun_facts", [])) > 0
        )
        if has_substance and info.get("persona") and len(info["persona"]) > 50:
            notable.append((handle, info))

    for handle, info in notable:
        name = info["name"]
        line = f"- **{name}** (@{handle}): "
        parts = []
        if info.get("projects"):
            parts.append(info["projects"][0])
        if info.get("persona"):
            # Take first sentence of persona
            first_sentence = info["persona"].split(". ")[0]
            parts.append(first_sentence)
        if info.get("memes"):
            parts.append(f"Memes: {', '.join(info['memes'][:2])}")
        if info.get("catchphrases"):
            parts.append(f'Says: "{info["catchphrases"][0]}"')
        line += " | ".join(parts)
        lines.append(line)

    # Add ecosystem context
    lines.append("")
    lines.append("### ECOSYSTEM CULTURE")
    for eco_name, eco in ECOSYSTEM_CONTEXT.items():
        lines.append(f"**{eco_name.title()}**: {eco.get('origin', '')}")
        for note in eco.get("culture", [])[:3]:
            lines.append(f"  - {note}")

    # Special inside jokes
    lines.append("")
    lines.append("### INSIDE JOKES TO USE")
    lines.append("- Tag @brentsketit and just say 'hey' or 'look' = community meme (do this occasionally)")
    lines.append("- The wassie stuffed animals near Mon = Maru's (@wasserpest) creation, they have 'room temperature IQ'")
    lines.append("- Mentioning someone's project/meme shows you KNOW them (e.g. ask Gabriel about shirtless rants)")
    lines.append("- billmonday's 'gmonad = disqualified' tweet is Monad lore")
    lines.append("- Tori (@bonecondor) is 'Chairman Birb Bernanke' - address her as such")
    lines.append("- Jintao's (@hellojintao) assets always 'trend towards zero' - commiserate")
    lines.append("- Matt (@cryptochefmatt) is an actual chef - 'time to cook' has double meaning")
    lines.append("- Drew (@drew_osumi) survived both MoviePass AND Fyre Festival - the man can't be stopped")

    return "\n".join(lines)
