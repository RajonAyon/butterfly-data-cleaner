"""
Build butterfly reference database from multiple sources.
"""

import sys
import os



# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)


import pandas as pd
from src.species_extraction import build_reference_database_from_pdf

# Manual additions (species not in PDF checklist)
common_to_scientific = {
    'Falcate Oakblue': ('Mahathala', 'ameria'),
    'Elbowed Pierrot': ('Caleta', 'elna'),
    'Purple Leaf Blue': ('Amblypodia', 'anita'),
    'Green Oakblue': ('Arhopala', 'eumolphus'),
    'Great Orange Tip': ('Hebomoia', 'glaucippe'),
    'Grass Bob': ('Suada', 'swerga'),
    'Paintbrush Swift': ('Baoris', 'farri'),
    'Dark Pierrot': ('Tarucus', 'ananda'),
    'Quaker': ('Neptis', 'harita'),
    'Copper Flash': ('Zographetus', 'dzonguensis'),
    'Lesser Gull': ('Cepora', 'nadina'),
    'Plain Earl': ('Tanaecia', 'lepidea'),
    'Jewelled Nawab': ('Polyura', 'delphis'),
    'Black-Spotted Pierrot': ('Tarucus', 'balkanicus'),
    'Rustic': ('Cupha', 'erymanthis'),
    'Striped Albatross': ('Appias', 'libythea'),
    'Common Mormon': ('Papilio', 'polytes'),
    'Centaur Oakblue': ('Arhopala', 'centaurus'),
    'Tawny Rajah': ('Charaxes', 'bernardus'),
    'Banded Ace': ('Dophla', 'evelina'),
    'Common Jay': ('Graphium', 'doson'),
    'Wax Dart': ('Cephrenes', 'chrysozona'),
    'Pallid Nawab': ('Polyura', 'arja'),
    'Common Spotted Flat': ('Celaenorrhinus', 'leucocera'),
    'Perak Lascar': ('Pantoporia', 'paraka'),
    'Plains Cupid': ('Zographetus', 'dzonguensis'),
    'Common Crow': ('Euploea', 'core'),
    'Orchid Tit': ('Zographetus', 'dzonguensis'),
    'Common Silverline': ('Spindasis', 'vulcanus'),
    'Yellow Orange-Tip': ('Ixias', 'pyrene'),
    'Monkey Puzzle': ('Zographetus', 'dzonguensis'),
    'Chain Swordtail': ('Graphium', 'nomius'),
    'Striped Blue Crow': ('Euploea', 'mulciber'),
    'Common Rose': ('Atrophaneura', 'horishana'),
    'Dark Cerulean': ('Jamides', 'alecto'),
    'Sullied Sailer': ('Neptis', 'soma'),
    'Small Green Awlet': ('Bibasis', 'amara'),
    'Dingiest Sailer': ('Neptis', 'harita'),
    'Dot-Dash Sergeant': ('Athyma', 'nefte'),
    'Long-Branded Blue Crow': ('Euploea', 'algae'),
    'Plain Puffin': ('Appias', 'indra'),
    'Plain Palm Dart': ('Cephrenes', 'acalle'),
    'White-Edged Blue Baron': ('Euthalia', 'phemius'),
    'Common Grass Dart': ('Taractrocera', 'maevius'),
    'Indigo Flash': ('Zographetus', 'dzonguensis'),
    'Common Pamfly': ('Elymnias', 'hypermnestra'),
    'Narrow-Banded Velvet Bob': ('Koruthaialos', 'rubecula'),
    'Plum Judy': ('Abisara', 'neophron'),
    'Magpie Crow': ('Euploea', 'radamanthus'),
    'Tree Yellow': ('Gandaca', 'harina'),
    'Common Cerulean': ('Jamides', 'celeno'),
    'Orange Awlet': ('Bibasis', 'harisa'),
    'Spot Swordtail': ('Graphium', 'nomius'),
    'Tamil Oakblue': ('Arhopala', 'bazaloides'),
    'Double-Tufted Royal': ('Tajuria', 'cippus'),
    'Silver Forget-Me-Not': ('Catochrysops', 'strabo'),
    "Double banded Judy":('Abisara','bifasciata'),
    "Plum Judy":('Abisara','echerius'),
    'Harlequin':('axila','haquinus'),
    'Punchinello':('Zemeros',"flegyas"),
    'Falcate Oakblue': ('Mahathala', 'ameria'),
    'Elbowed Pierrot': ('Caleta', 'elna'),
    'Purple Leaf Blue': ('Amblypodia', 'anita'),
    'Green Oakblue': ('Arhopala', 'eumolphus'),
    'Great Orange Tip': ('Hebomoia', 'glaucippe'),
    'Grass Bob': ('Suada', 'swerga'),
    'Paintbrush Swift': ('Baoris', 'farri'),
    'Dark Pierrot': ('Tarucus', 'ananda'),
    'Quaker': ('Neptis', 'harita'),
    'Copper Flash': ('Zographetus', 'dzonguensis'),
    'Lesser Gull': ('Cepora', 'nadina'),
    'Plain Earl': ('Tanaecia', 'lepidea'),
    'Jewelled Nawab': ('Polyura', 'delphis'),
    'Black-Spotted Pierrot': ('Tarucus', 'balkanicus'),
    'Rustic': ('Cupha', 'erymanthis'),
    'Striped Albatross': ('Appias', 'libythea'),
    'Common Mormon': ('Papilio', 'polytes'),
    'Centaur Oakblue': ('Arhopala', 'centaurus'),
    'Tawny Rajah': ('Charaxes', 'bernardus'),
    'Banded Ace': ('Dophla', 'evelina'),
    'Common Jay': ('Graphium', 'doson'),
    'Wax Dart': ('Cephrenes', 'chrysozona'),
    'Pallid Nawab': ('Polyura', 'arja'),
    'Common Spotted Flat': ('Celaenorrhinus', 'leucocera'),
    'Perak Lascar': ('Pantoporia', 'paraka'),
    'Plains Cupid': ('Zographetus', 'dzonguensis'),
    'Common Crow': ('Euploea', 'core'),
    'Orchid Tit': ('Zographetus', 'dzonguensis'),
    'Common Silverline': ('Spindasis', 'vulcanus'),
    'Yellow Orange-Tip': ('Ixias', 'pyrene'),
    'Monkey Puzzle': ('Zographetus', 'dzonguensis'),
    'Chain Swordtail': ('Graphium', 'nomius'),
    'Striped Blue Crow': ('Euploea', 'mulciber'),
    'Common Rose': ('Atrophaneura', 'horishana'),
    'Dark Cerulean': ('Jamides', 'alecto'),
    'Sullied Sailer': ('Neptis', 'soma'),
    'Small Green Awlet': ('Bibasis', 'amara'),
    'Dingiest Sailer': ('Neptis', 'harita'),
    'Dot-Dash Sergeant': ('Athyma', 'nefte'),
    'Long-Branded Blue Crow': ('Euploea', 'algae'),
    'Plain Puffin': ('Appias', 'indra'),
    'Plain Palm Dart': ('Cephrenes', 'acalle'),
    'White-Edged Blue Baron': ('Euthalia', 'phemius'),
    'Common Grass Dart': ('Taractrocera', 'maevius'),
    'Indigo Flash': ('Zographetus', 'dzonguensis'),
    'Common Pamfly': ('Elymnias', 'hypermnestra'),
    'Narrow-Banded Velvet Bob': ('Koruthaialos', 'rubecula'),
    'Plum Judy': ('Abisara', 'neophron'),
    'Magpie Crow': ('Euploea', 'radamanthus'),
    'Tree Yellow': ('Gandaca', 'harina'),
    'Common Cerulean': ('Jamides', 'celeno'),
    'Orange Awlet': ('Bibasis', 'harisa'),
    'Spot Swordtail': ('Graphium', 'nomius'),
    'Tamil Oakblue': ('Arhopala', 'bazaloides'),
    'Double-Tufted Royal': ('Tajuria', 'cippus'),
    'Silver Forget-Me-Not': ('Catochrysops', 'strabo')
}



# Build reference database
reference_df = build_reference_database_from_pdf(
    pdf_path='data/A_Checklist_of_Butterflies_of_Bangladesh.pdf',
    pages='1-10',
    additional_species=common_to_scientific,
    photographic_guide_csv='data/Photographicguide.csv',
    output_path='data/main_butterfly_list.csv'
)

print(f"Total species in database: {len(reference_df)}")



