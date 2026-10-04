"""Seed realistic Class 11-12 questions for every subject."""
import json
from .database import SessionLocal, engine, Base
from .models import Question, User
from .auth import hash_password

STREAMS = {
    "Science Medical": ["Physics", "Chemistry", "Biology"],
    "Science Non-Medical": ["Physics", "Chemistry", "Mathematics", "Computer Science"],
    "Commerce": ["Accountancy", "Business Studies", "Economics", "Mathematics"],
    "Humanities": ["History", "Political Science", "Geography", "Sociology", "Psychology"],
}

CANONICAL_STREAM = {
    "Physics": "Science Non-Medical", "Chemistry": "Science Non-Medical",
    "Biology": "Science Medical", "Mathematics": "Science Non-Medical",
    "Computer Science": "Science Non-Medical", "Accountancy": "Commerce",
    "Business Studies": "Commerce", "Economics": "Commerce",
    "History": "Humanities", "Political Science": "Humanities",
    "Geography": "Humanities", "Sociology": "Humanities", "Psychology": "Humanities",
}


def Q(question, options, answer, subject, topic, difficulty, expected_time, explanation, hint=""):
    return dict(question=question, options=options, answer=answer, subject=subject,
                stream=CANONICAL_STREAM[subject], topic=topic, difficulty=difficulty,
                expected_time=expected_time, explanation=explanation, hint=hint)


QUESTIONS = [
    # ---------------- PHYSICS (10) ----------------
    Q("A car moves with uniform velocity of 20 m/s for 10 s. Distance covered?", ["100 m","200 m","150 m","20 m"], 1, "Physics", "Kinematics", "easy", 15, "Distance = velocity × time = 20 × 10 = 200 m.", "Use d = v × t."),
    Q("SI unit of force?", ["Joule","Newton","Watt","Pascal"], 1, "Physics", "Laws of Motion", "easy", 10, "Force is measured in Newton (kg·m/s²).", "Named after Newton."),
    Q("A projectile is launched at 45°. For maximum range, angle should be?", ["30°","45°","60°","90°"], 1, "Physics", "Projectile Motion", "medium", 20, "Range R = u²sin2θ/g is maximum when sin2θ=1, i.e. θ=45°.", "Recall R formula."),
    Q("Work done when force of 10 N displaces body by 5 m in its direction?", ["2 J","15 J","50 J","0 J"], 2, "Physics", "Work & Energy", "medium", 20, "W = F·d = 10 × 5 = 50 J.", "W = Fd cosθ, θ=0."),
    Q("Current through 4Ω resistor with 12 V across it?", ["48 A","3 A","8 A","0.33 A"], 1, "Physics", "Current Electricity", "medium", 20, "Ohm's law: I = V/R = 12/4 = 3 A.", "Use I = V/R."),
    Q("Escape velocity from Earth is approximately?", ["7.9 km/s","11.2 km/s","3.1 km/s","22.4 km/s"], 1, "Physics", "Gravitation", "hard", 25, "Escape velocity = √(2gR) ≈ 11.2 km/s for Earth.", "About 11 km/s."),
    Q("A 2 kg mass has kinetic energy 36 J. Its speed is?", ["6 m/s","9 m/s","18 m/s","4 m/s"], 0, "Physics", "Work & Energy", "hard", 30, "KE = ½mv² → 36 = ½·2·v² → v²=36 → v=6 m/s.", "Solve ½mv²."),
    Q("Two capacitors 2µF and 3µF in series. Equivalent capacitance?", ["5 µF","1.2 µF","6 µF","0.8 µF"], 1, "Physics", "Electrostatics", "hard", 30, "1/C = 1/2+1/3 = 5/6 → C = 6/5 = 1.2 µF.", "Series: reciprocals add."),
    Q("An AC circuit draws maximum power when?", ["Purely resistive","Purely inductive","At resonance X_L = X_C","Zero resistance"], 2, "Physics", "Alternating Current", "expert", 40, "At resonance inductive and capacitive reactances cancel, impedance is minimum and power factor is 1.", "Think resonance."),
    Q("De Broglie wavelength of electron accelerated through 150 V is about?", ["1 Å","0.5 Å","2 Å","10 Å"], 0, "Physics", "Dual Nature", "expert", 45, "λ = 12.27/√V Å = 12.27/√150 ≈ 1 Å.", "λ = 12.27/√V angstrom."),
    # ---------------- CHEMISTRY (10) ----------------
    Q("Atomic number of Carbon?", ["6","12","14","8"], 0, "Chemistry", "Atomic Structure", "easy", 10, "Carbon has 6 protons, so atomic number is 6.", "Count protons."),
    Q("pH of neutral solution at 25°C?", ["0","7","14","1"], 1, "Chemistry", "Acids & Bases", "easy", 10, "Neutral solution has [H⁺]=10⁻⁷ M, so pH = 7.", "Midpoint of 0–14."),
    Q("Which is an alkane?", ["C₂H₄","C₂H₆","C₂H₂","C₆H₆"], 1, "Chemistry", "Hydrocarbons", "medium", 20, "Alkanes follow CₙH₂ₙ₊₂; ethane C₂H₆ qualifies.", "Check CₙH₂ₙ₊₂."),
    Q("Molarity of 58.5 g NaCl in 1 L solution? (M = 58.5)", ["0.5 M","1 M","2 M","5.85 M"], 1, "Chemistry", "Mole Concept", "medium", 20, "Moles = 58.5/58.5 = 1 mol in 1 L → 1 M.", "Moles ÷ volume."),
    Q("Hybridisation of carbon in methane (CH₄)?", ["sp","sp²","sp³","dsp²"], 2, "Chemistry", "Chemical Bonding", "medium", 20, "CH₄ has 4 sigma bonds, tetrahedral, sp³ hybridised.", "4 bond pairs."),
    Q("Which element has highest electronegativity?", ["Oxygen","Fluorine","Chlorine","Nitrogen"], 1, "Chemistry", "Periodicity", "hard", 25, "Fluorine (3.98) is the most electronegative element.", "Top-right of periodic table."),
    Q("For reaction N₂+3H₂⇌2NH₃, Kₚ and Kc relation?", ["Kₚ=Kc(RT)⁻²","Kₚ=Kc(RT)²","Kₚ=Kc","Kₚ=Kc(RT)⁻¹"], 0, "Chemistry", "Equilibrium", "hard", 30, "Kₚ = Kc(RT)^Δn, Δn = 2−4 = −2.", "Δn = products − reactants."),
    Q("IUPAC name of CH₃–CH(OH)–CH₃?", ["Propan-1-ol","Propan-2-ol","Ethanol","Acetone"], 1, "Chemistry", "Alcohols", "hard", 25, "OH on carbon 2 of propane → propan-2-ol.", "Number to give OH lowest locant."),
    Q("Standard electrode potential of SHE is?", ["1.00 V","0.00 V","−0.76 V","+0.34 V"], 1, "Chemistry", "Electrochemistry", "expert", 35, "Standard Hydrogen Electrode is the reference at 0.00 V.", "It is the reference."),
    Q("Rate constant unit for second-order reaction?", ["s⁻¹","mol⁻¹ L s⁻¹","mol L⁻¹ s⁻¹","unitless"], 1, "Chemistry", "Kinetics", "expert", 40, "For order n, unit is mol^(1−n) L^(n−1) s⁻¹; n=2 → mol⁻¹ L s⁻¹.", "Use rate = k[A]²."),
    # ---------------- BIOLOGY (9) ----------------
    Q("Powerhouse of the cell?", ["Nucleus","Ribosome","Mitochondria","Chloroplast"], 2, "Biology", "Cell Biology", "easy", 10, "Mitochondria produce ATP by cellular respiration.", "Makes ATP."),
    Q("Functional unit of kidney?", ["Neuron","Nephron","Alveolus","Glomerulus only"], 1, "Biology", "Excretion", "easy", 12, "Nephron is the structural and functional unit of kidney.", "Filters blood."),
    Q("Hormone regulating blood sugar?", ["Thyroxine","Insulin","Adrenaline","Growth hormone"], 1, "Biology", "Coordination", "medium", 18, "Insulin from pancreatic β-cells lowers blood glucose.", "From pancreas."),
    Q("Site of photosynthesis?", ["Mitochondria","Chloroplast","Nucleus","Vacuole"], 1, "Biology", "Photosynthesis", "medium", 15, "Chlorophyll in chloroplasts traps light energy.", "Contains chlorophyll."),
    Q("DNA double helix was proposed by?", ["Darwin & Wallace","Watson & Crick","Lamarck","Morgan"], 1, "Biology", "Genetics", "medium", 18, "Watson and Crick (1953) using Franklin's data.", "1953 model."),
    Q("Cross Rr × Rr gives phenotypic ratio?", ["1:1","3:1","9:3:3:1","1:2:1"], 1, "Biology", "Genetics", "hard", 25, "Monohybrid cross: 3 dominant : 1 recessive.", "Punnett square."),
    Q("Oxygen binds haemoglobin at?", ["Calcium site","Haem iron","Globin tail","Plasma"], 1, "Biology", "Circulation", "hard", 25, "Each haem group has Fe²⁺ binding one O₂.", "Fe²⁺ in haem."),
    Q("Which is a primary lymphoid organ?", ["Spleen","Bone marrow","Tonsils"," appendix"], 1, "Biology", "Immunity", "expert", 35, "Bone marrow and thymus are primary lymphoid organs.", "Where lymphocytes mature."),
    Q("Net ATP gain from aerobic respiration of one glucose?", ["2","8","30–32","4"], 2, "Biology", "Respiration", "expert", 40, "Glycolysis + Krebs + ETS yields about 30–32 ATP.", "Count ETS yield."),
    # ---------------- MATHEMATICS (10) ----------------
    Q("Derivative of x²?", ["x","2x","x²","2"], 1, "Mathematics", "Differentiation", "easy", 12, "Power rule: d/dx[xⁿ] = n·xⁿ⁻¹ → 2x.", "Power rule."),
    Q("Value of sin 30°?", ["1","0","1/2","√3/2"], 2, "Mathematics", "Trigonometry", "easy", 10, "Standard value sin 30° = 1/2.", "Standard triangle."),
    Q("Derivative of x² + 3x?", ["2x+3","x+3","2x","x²+3"], 0, "Mathematics", "Differentiation", "medium", 20, "d/dx[x²]=2x and d/dx[3x]=3, sum = 2x+3.", "Differentiate term by term."),
    Q("∫ 2x dx = ?", ["x² + C","2x² + C","x + C","2 + C"], 0, "Mathematics", "Integration", "medium", 20, "∫xⁿ dx = xⁿ⁺¹/(n+1); ∫2x dx = x² + C.", "Reverse power rule."),
    Q("Probability of getting a head in one coin toss?", ["1","1/2","1/4","0"], 1, "Mathematics", "Probability", "medium", 12, "One favourable of two equally likely outcomes.", "Favourable/total."),
    Q("If A = {1,2}, number of subsets?", ["2","3","4","1"], 2, "Mathematics", "Sets", "hard", 20, "n(A)=2 → 2² = 4 subsets.", "2ⁿ rule."),
    Q("Limit x→0 of sin x / x?", ["0","1","∞","Does not exist"], 1, "Mathematics", "Limits", "hard", 25, "Standard limit equals 1.", "Standard result."),
    Q("Matrix [[1,2],[3,4]] determinant?", ["−2","10","−10","2"], 0, "Mathematics", "Matrices", "hard", 25, "det = 1·4 − 2·3 = −2.", "ad − bc."),
    Q("Solution of differential equation dy/dx = y?", ["y = Ceˣ","y = x + C","y = ln x","y = eˣ + x"], 0, "Mathematics", "Differential Equations", "expert", 40, "dy/y = dx → ln y = x + c → y = Ceˣ.", "Separate variables."),
    Q("Number of ways to arrange 5 books in a row?", ["25","10","120","60"], 2, "Mathematics", "Permutations", "expert", 35, "5! = 120.", "Factorial."),
    # ---------------- COMPUTER SCIENCE (9) ----------------
    Q("Which is an input device?", ["Monitor","Keyboard","Printer","Speaker"], 1, "Computer Science", "Basics", "easy", 10, "Keyboard sends data into the computer.", "Sends data in."),
    Q("Python: type of 3.14?", ["int","float","str","bool"], 1, "Computer Science", "Python", "easy", 10, "Decimal numbers are float in Python.", "Decimal type."),
    Q("Output of print(2 ** 3)?", ["6","8","5","9"], 1, "Computer Science", "Python", "medium", 15, "** is exponentiation: 2³ = 8.", "** means power."),
    Q("Which data structure is LIFO?", ["Queue","Stack","Array","Tree"], 1, "Computer Science", "Data Structures", "medium", 18, "Stack: Last In First Out.", "Push/pop."),
    Q("Time complexity of binary search?", ["O(n)","O(n²)","O(log n)","O(1)"], 2, "Computer Science", "Algorithms", "medium", 20, "Halving each step gives logarithmic time.", "Halves search space."),
    Q("Output of len([1,2,3]) in Python?", ["1","2","3","Error"], 2, "Computer Science", "Python", "hard", 20, "List has 3 elements.", "Count items."),
    Q("Which SQL command retrieves data?", ["GET","SELECT","FETCH","EXTRACT"], 1, "Computer Science", "Databases", "hard", 20, "SELECT queries rows from tables.", "Query keyword."),
    Q("In OOP, bundling data + methods is?", ["Inheritance","Encapsulation","Polymorphism","Abstraction"], 1, "Computer Science", "OOP", "expert", 30, "Encapsulation wraps data and methods together.", "Capsule analogy."),
    Q("Worst-case complexity of quicksort?", ["O(n log n)","O(n²)","O(n)","O(log n)"], 1, "Computer Science", "Algorithms", "expert", 35, "Bad pivots degrade quicksort to O(n²).", "Unbalanced partitions."),
    # ---------------- ACCOUNTANCY (8) ----------------
    Q("Accounting equation?", ["A = L − C","A = L + C","L = A + C","C = A − L + P"], 1, "Accountancy", "Basics", "easy", 12, "Assets = Liabilities + Capital.", "A = L + Capital."),
    Q("Debit means?", ["Increase in asset","Decrease in asset","Increase in liability","No change"], 0, "Accountancy", "Journal", "easy", 12, "Debit increases assets/expenses.", "Left side."),
    Q("Trial balance checks?", ["Profit","Arithmetical accuracy","Cash only","Stock"], 1, "Accountancy", "Trial Balance", "medium", 18, "Trial balance verifies debit = credit accuracy.", "Debits = credits?"),
    Q("Depreciation is charged on?", ["Current assets","Fixed assets","Fictitious assets","Stock"], 1, "Accountancy", "Depreciation", "medium", 18, "Fixed assets depreciate over useful life.", "Long-term assets."),
    Q("Bank reconciliation matches?", ["Cash book & pass book","Journal & ledger","Trial & balance sheet","Sales & purchase"], 0, "Accountancy", "BRS", "medium", 18, "BRS reconciles cash book with bank pass book.", "Bank vs books."),
    Q("Straight-line depreciation: cost 50000, scrap 5000, life 9 yrs?", ["5000","4500","5500","9000"], 0, "Accountancy", "Depreciation", "hard", 30, "(50000−5000)/9 = 5000 per year.", "(Cost − scrap)/life."),
    Q("Which error affects trial balance?", ["Omission","Partial omission of posting","Compensating","Principle"], 1, "Accountancy", "Rectification", "hard", 30, "Posting debit without credit (partial omission) unbalances totals.", "One-sided error."),
    Q("Partnership deed is?", ["Optional but desirable","Compulsory","Illegal","Verbal only"], 0, "Accountancy", "Partnership", "expert", 30, "A written deed is not compulsory but strongly desirable.", "Written agreement."),
    # ---------------- BUSINESS STUDIES (8) ----------------
    Q("Management is?", ["Art only","Art + Science","Neither","Only science"], 1, "Business Studies", "Management", "easy", 12, "Management is both an art and a science.", "Applies knowledge skilfully."),
    Q("Father of Scientific Management?", ["Fayol","Taylor","Weber","Mayo"], 1, "Business Studies", "Principles", "easy", 12, "F.W. Taylor introduced scientific management.", "Time studies."),
    Q("Planning is?", ["Primary function","Last function","Optional","Waste"], 0, "Business Studies", "Planning", "medium", 15, "Planning is the primary, first function of management.", "First step."),
    Q("Span of control means?", ["No. of subordinates a manager handles","Total staff","Profit margin","Market share"], 0, "Business Studies", "Organising", "medium", 18, "Span = number of direct subordinates.", "Direct reports."),
    Q("Maslow's highest need?", ["Safety","Self-actualisation","Social","Esteem"], 1, "Business Studies", "Motivation", "medium", 18, "Self-actualisation tops the hierarchy.", "Top of pyramid."),
    Q("Which is a short-term source of finance?", ["Equity","Debentures","Trade credit","Bonds"], 2, "Business Studies", "Finance", "hard", 25, "Trade credit is short-term supplier financing.", "Supplier credit."),
    Q("Marketing mix 4Ps excludes?", ["Product","Price","People","Place"], 2, "Business Studies", "Marketing", "hard", 25, "Classic 4Ps: Product, Price, Place, Promotion.", "4Ps list."),
    Q("SEBI regulates?", ["Banks","Securities market","Insurance only","RBI"], 1, "Business Studies", "Business Environment", "expert", 30, "SEBI protects investors in securities markets.", "Stock market regulator."),
    # ---------------- ECONOMICS (8) ----------------
    Q("Scarcity means?", ["No resources","Limited resources vs unlimited wants","Free goods","Surplus"], 1, "Economics", "Basics", "easy", 12, "Economics studies choice under scarcity.", "Wants > resources."),
    Q("Law of demand: price rises, quantity?", ["Rises","Falls","Unchanged","Zero"], 1, "Economics", "Demand", "easy", 12, "Inverse price–demand relationship.", "Downward sloping curve."),
    Q("GDP stands for?", ["Gross Domestic Product","General Domestic Price","Gross Demand Production","Global Domestic Product"], 0, "Economics", "National Income", "medium", 15, "GDP = market value of final goods/services in a year.", "Final output measure."),
    Q("Inflation means?", ["Falling prices","Sustained rise in general prices","More exports","Less money"], 1, "Economics", "Money & Banking", "medium", 18, "Inflation is a persistent general price rise.", "Prices rise."),
    Q("Opportunity cost is?", ["Money spent","Next best alternative forgone","Total cost","Fixed cost"], 1, "Economics", "Basics", "medium", 18, "Value of the next best alternative sacrificed.", "What you give up."),
    Q("If elasticity = 1.5, demand is?", ["Inelastic","Unitary","Elastic","Perfectly inelastic"], 2, "Economics", "Elasticity", "hard", 25, "|e|>1 means elastic demand.", ">1 → elastic."),
    Q("Repo rate is fixed by?", ["SBI","RBI","Government directly","SEBI"], 1, "Economics", "Money & Banking", "hard", 25, "RBI sets repo rate in monetary policy.", "Central bank."),
    Q("Gini coefficient measures?", ["Growth","Income inequality","Inflation","Literacy"], 1, "Economics", "Development", "expert", 35, "Gini 0 (equal) to 1 (unequal) measures inequality.", "0 = equality."),
    # ---------------- HISTORY (8) ----------------
    Q("First War of Independence year?", ["1857","1947","1757","1920"], 0, "History", "Modern India", "easy", 12, "The 1857 revolt began at Meerut.", "Sepoy Mutiny year."),
    Q("Founder of Maurya Empire?", ["Ashoka","Chandragupta Maurya","Bindusara","Kanishka"], 1, "History", "Ancient India", "easy", 12, "Chandragupta Maurya founded it c. 321 BCE.", "With Chanakya's help."),
    Q("Gandhi launched Dandi March in?", ["1920","1930","1942","1919"], 1, "History", "National Movement", "medium", 18, "Salt March: March–April 1930.", "Salt satyagraha."),
    Q("Harappa is located in present-day?", ["India","Pakistan","Nepal","Bangladesh"], 1, "History", "Indus Valley", "medium", 15, "Harappa is in Punjab, Pakistan.", "Across the border."),
    Q("Who wrote Arthashastra?", ["Kalidas","Kautilya","Panini","Aryabhata"], 1, "History", "Ancient India", "medium", 18, "Kautilya (Chanakya) wrote on statecraft.", "Chandragupta's minister."),
    Q("Battle of Plassey year?", ["1757","1764","1772","1857"], 0, "History", "Modern India", "hard", 20, "Clive defeated Siraj-ud-daulah in 1757.", "Before Buxar (1764)."),
    Q("Quit India Movement launched in?", ["1930","1942","1947","1922"], 1, "History", "National Movement", "hard", 20, "'Do or Die' call in August 1942.", "Do or Die."),
    Q("Vienna Congress year?", ["1815","1789","1848","1919"], 0, "History", "World History", "expert", 30, "After Napoleon's defeat, 1815 settlement.", "After Waterloo era."),
    # ---------------- POLITICAL SCIENCE (8) ----------------
    Q("Indian Constitution adopted on?", ["15 Aug 1947","26 Nov 1949","26 Jan 1950","2 Oct 1949"], 1, "Political Science", "Constitution", "easy", 12, "Adopted 26 Nov 1949, enforced 26 Jan 1950.", "Adoption vs enforcement."),
    Q("Lower house of Parliament?", ["Rajya Sabha","Lok Sabha","Vidhan Sabha","Council"], 1, "Political Science", "Legislature", "easy", 10, "Lok Sabha is the directly elected lower house.", "Direct elections."),
    Q("Fundamental Rights are in?", ["Part III","Part IV","Part II","Part V"], 0, "Political Science", "Constitution", "medium", 15, "Part III (Articles 12–35).", "Justiciable rights."),
    Q("Minimum voting age in India?", ["21","18","25","16"], 1, "Political Science", "Democracy", "medium", 12, "Lowered to 18 by 61st Amendment (1988).", "61st Amendment."),
    Q("Head of state (de jure) in India?", ["Prime Minister","President","Chief Justice","Speaker"], 1, "Political Science", "Executive", "medium", 15, "President is constitutional head; PM is real executive.", "Nominal head."),
    Q("Panchayati Raj established by?", ["42nd Amendment","73rd Amendment","52nd Amendment","44th Amendment"], 1, "Political Science", "Local Governance", "hard", 25, "73rd Amendment (1992) gave constitutional status.", "1992 reform."),
    Q("First-past-the-post is used for?", ["Lok Sabha elections","Rajya Sabha","President","Vice-President"], 0, "Political Science", "Electoral System", "hard", 25, "Lok Sabha uses plurality/FPTP in single-member seats.", "Most votes wins seat."),
    Q("Directive Principles are?", ["Justiciable","Non-justiciable","Fundamental rights","Emergency provisions"], 1, "Political Science", "Constitution", "expert", 30, "DPSPs (Part IV) guide the state but aren't court-enforceable.", "Moral guidelines."),
    # ---------------- GEOGRAPHY (8) ----------------
    Q("Largest planet?", ["Earth","Jupiter","Saturn","Mars"], 1, "Geography", "Solar System", "easy", 10, "Jupiter is the largest planet.", "Gas giant."),
    Q("Tropic of Cancer passes through?", ["Kerala","Madhya Pradesh","Kashmir","Tamil Nadu"], 1, "Geography", "India", "easy", 12, "It passes through MP, Gujarat, Rajasthan, etc.", "Central India."),
    Q("Longest river in India?", ["Yamuna","Ganga","Brahmaputra","Godavari"], 1, "Geography", "Rivers", "medium", 15, "Ganga (~2525 km) is longest within India.", "Plains river."),
    Q("Richter scale measures?", ["Rainfall","Earthquakes","Wind","Temperature"], 1, "Geography", "Disasters", "medium", 12, "Richter measures earthquake magnitude.", "Seismic waves."),
    Q("Tea grows best in?", ["Black soil","Laterite soil","Alluvial","Desert"], 1, "Geography", "Agriculture", "medium", 18, "Well-drained laterite soils suit tea.", "Hilly plantations."),
    Q("Sundarbans famous for?", ["Lions","Mangroves & Royal Bengal Tiger","Cactus","Elephants"], 1, "Geography", "Environment", "hard", 20, "Mangrove delta habitat of the Bengal tiger.", "Delta mangroves."),
    Q("El Niño affects?", ["Indian monsoon","Tides only","Glaciers only","Ozone"], 0, "Geography", "Climate", "hard", 25, "El Niño warming often weakens the Indian monsoon.", "Pacific warming."),
    Q("Contour lines show?", ["Temperature","Elevation","Rainfall","Pressure"], 1, "Geography", "Maps", "expert", 30, "Contours join points of equal elevation.", "Equal height lines."),
    # ---------------- SOCIOLOGY (7) ----------------
    Q("Sociology studies?", ["Cells","Society & social behaviour","Stars","Rocks"], 1, "Sociology", "Basics", "easy", 10, "Sociology studies society, institutions and interactions.", "Society."),
    Q("Father of Sociology?", ["Marx","Auguste Comte","Durkheim","Weber"], 1, "Sociology", "Thinkers", "easy", 12, "Comte coined 'sociology'.", "Coined the term."),
    Q("Primary group example?", ["Factory","Family","Political party","Crowd"], 1, "Sociology", "Groups", "medium", 15, "Family involves intimate face-to-face ties (Cooley).", "Close-knit."),
    Q("'Protestant Ethic' author?", ["Marx","Weber","Durkheim","Comte"], 1, "Sociology", "Thinkers", "medium", 18, "Max Weber linked Protestant ethics to capitalism.", "Capitalism study."),
    Q("Sanskritisation concept by?", ["M.N. Srinivas","Ghurye","Ambedkar","Marx"], 0, "Sociology", "Indian Society", "hard", 25, "Srinivas described lower castes emulating upper-caste practices.", "Caste mobility."),
    Q("Anomie means?", ["Order","Normlessness","Harmony","Tradition"], 1, "Sociology", "Concepts", "hard", 25, "Durkheim's anomie = breakdown of norms.", "Norm breakdown."),
    Q("Stratification based on birth in India?", ["Class","Caste","Gender roles only","Slavery"], 1, "Sociology", "Stratification", "expert", 30, "Caste is hereditary, endogamous stratification.", "Birth-based."),
    # ---------------- PSYCHOLOGY (7) ----------------
    Q("Study of behaviour & mental processes?", ["Sociology","Psychology","Biology","Economics"], 1, "Psychology", "Basics", "easy", 10, "Psychology studies behaviour and mind.", "Mind + behaviour."),
    Q("Founder of psychoanalysis?", ["Skinner","Freud","Pavlov","Jung"], 1, "Psychology", "Approaches", "easy", 12, "Sigmund Freud founded psychoanalysis.", "Id, ego, superego."),
    Q("Classical conditioning by?", ["Skinner","Pavlov","Bandura","Maslow"], 1, "Psychology", "Learning", "medium", 15, "Pavlov's dogs: bell → salivation.", "Dogs experiment."),
    Q("Short-term memory capacity (Miller)?", ["2±1","7±2","15±2","Unlimited"], 1, "Psychology", "Memory", "medium", 18, "Miller's magical number 7±2 chunks.", "Magical number 7."),
    Q("IQ formula?", ["MA/CA × 100","CA/MA × 100","MA + CA","MA × CA"], 0, "Psychology", "Intelligence", "hard", 20, "Stern: IQ = mental age / chronological age × 100.", "Ratio × 100."),
    Q("Hierarchy of needs by?", ["Freud","Maslow","Rogers","Erikson"], 1, "Psychology", "Motivation", "hard", 20, "Maslow's pyramid: physiological → self-actualisation.", "Pyramid."),
    Q("Fundamental attribution error is?", ["Overemphasising traits over situation","Ignoring traits","Perfect judgement","Memory loss"], 0, "Psychology", "Social Psychology", "expert", 30, "We over-attribute others' behaviour to disposition.", "Blame character."),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Question).count() >= len(QUESTIONS):
            print("Questions already seeded.")
        else:
            db.query(Question).delete()
            for q in QUESTIONS:
                db.add(Question(
                    question=q["question"], options=json.dumps(q["options"]),
                    answer=q["answer"], subject=q["subject"], stream=q["stream"],
                    topic=q["topic"], difficulty=q["difficulty"],
                    expected_time=q["expected_time"], explanation=q["explanation"],
                    hint=q.get("hint", "")))
            db.commit()
            print(f"Seeded {len(QUESTIONS)} questions.")
        if not db.query(User).filter_by(email="admin@adaptiveai.school").first():
            db.add(User(name="Teacher Admin", email="admin@adaptiveai.school",
                        password_hash=hash_password("admin123"), stream="Science Non-Medical",
                        student_class="12", is_admin=True, current_tier=6, tier_progress=80))
            db.commit()
            print("Admin created: admin@adaptiveai.school / admin123")
        if not db.query(User).filter_by(email="ayushi@demo.school").first():
            db.add(User(name="Ayushi", email="ayushi@demo.school",
                        password_hash=hash_password("demo1234"), stream="Science Non-Medical",
                        student_class="12", reward_points=340, current_tier=4, tier_progress=72.0))
            db.commit()
            print("Demo student: ayushi@demo.school / demo1234")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
