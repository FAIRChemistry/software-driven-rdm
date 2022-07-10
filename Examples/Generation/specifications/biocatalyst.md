# Biocatalyst

Do fugiat mollit sit duis deserunt dolor ex. Quis do occaecat dolor consectetur nostrud occaecat eu sint aute. Laboris commodo laborum proident id laboris cupidatat amet commodo tempor laborum sint occaecat mollit velit. 

### BiocatalystBase

Do fugiat mollit sit duis deserunt dolor ex. Quis do occaecat dolor consectetur nostrud occaecat eu sint aute. Laboris commodo laborum proident id laboris cupidatat amet commodo tempor laborum sint occaecat mollit velit. 

- __name*__
  - Type: string
  - Description: Name of the biocatalyst
- __ecnumber__
  - Type: string
  - Description: Code used to determine the family of a protein.
- __reaction*__
  - Type: string
  - Description: Reaction in which the biocatalyst is activ.
- __sequence*__
  - Type: string
  - Description: Amino acid sequence of the biocatalyst.
- __host_organism*__
  - Type: string
  - Description: Organism used for expression.
- __source_organism*__
  - Type: string
  - Description: Organism the biocatalyst originates from.
- __post_translational_mods__
  - Type: string
  - Description: Post-translational modifications that were made.
- __production_procedure*__
  - Type: string
  - Description: Procedure on how the biocatalyst was synthesized/expressed.
- __isoenzyme*__
  - Type: string
  - Description: Isoenzyme of the biocatalyst.
- __tissue__
  - Type: string
  - Description: Tissue in which the reaction is happening.
- __localisation__
  - Type: string
  - Description: Localisation of the biocatalyst.

### SolubleBiocatalyst [_BiocatalystBase_]

Irure dolore dolore non sit adipisicing anim commodo est laborum. Proident do do velit eiusmod. Amet aliquip mollit aliqua voluptate eu. Proident ut id Lorem fugiat fugiat cillum ex. Aliqua excepteur laborum quis qui minim esse. Proident magna nostrud pariatur eiusmod nisi excepteur cillum sunt ad deserunt sint culpa ut proident. Esse ex qui occaecat aliquip ipsum exercitation amet ullamco laborum ea commodo exercitation do.

- __storage*__
  - Type: StorageConditions
  - Multiple: True
  - Description: How the soluble biocatalyst has been stored.
- __concentration*__
  - Type: posfloat
  - Description: Concentration of the biocatalyst.
- __concentration_det_method*__
  - Type: string
  - Description: Method on how the concentration has been determined.

### ImmobilisedCatalyst [_SolubleBiocatalyst_]

Laboris aliquip cupidatat id aliqua magna. Minim consectetur enim dolor qui laborum aute nisi. Sit quis aute aliquip labore anim quis consequat consequat anim nulla consequat in Lorem. Fugiat cupidatat nostrud nostrud enim in. Proident in fugiat excepteur elit quis laboris nostrud veniam cillum elit culpa. Excepteur qui irure ipsum eu. Officia exercitation ut dolor anim nulla Lorem ut incididunt amet aute do.

- __purification*__
  - Type: string
  - Description: How the biocatalyst was purified.
- __immobilisation_procedure*__
  - Type: string
  - Description: How the biocatalyst was immobilised

### CrudeCellExtract [_SolubleBiocatalyst_]

Fugiat fugiat nulla mollit officia exercitation adipisicing et labore proident nostrud proident fugiat. Voluptate esse mollit nulla tempor proident laborum et voluptate eu sit commodo. Elit consequat consectetur excepteur nulla irure qui. Proident labore esse ipsum Lorem eiusmod labore tempor consequat est esse deserunt. Fugiat aliqua sit tempor incididunt qui.

- __cell_disruption_process*__
  - Type: string
  - Description: Method used to disrupt cells.
- __purity_determination__
  - Type: string
  - Description: Method that was used to determine the purity of the extract.
  
### WholeCell [_BiocatalystBase_]

Fugiat dolor enim aute dolore tempor consectetur commodo commodo occaecat pariatur aute. Incididunt aliqua do ipsum proident do aute cupidatat tempor voluptate mollit eiusmod sunt. Quis duis mollit anim ex nulla enim minim. Incididunt qui commodo cupidatat occaecat dolor ipsum excepteur sint fugiat minim. Enim ipsum adipisicing ut proident enim sunt non.

- __harvesting_method*__
  - Type: string
  - Description: How the cells were harvested.

### StorageConditions

Ut aute ut Lorem veniam proident. Laborum do nisi ut eiusmod in nostrud proident. Commodo nulla ipsum commodo culpa aliqua dolore. Labore exercitation eiusmod ea do tempor. Eiusmod enim mollit sit enim eiusmod anim excepteur veniam culpa minim dolor. Labore aliquip sint laboris quis mollit nostrud cillum dolore elit sunt pariatur aliquip.

- __temperature__
  - Type: string
  - Description: Temperature of thet storage
- __storing_start__
  - Type: date
  - Description: Date when catalyst was put into storage.
- __removing__
  - Type: date
  - Description: Date when catalyst was removed from storage.
- __rethawing__
  - Type: date
  - Description: Date when catalyst was rethawed from storage.
- __thawing_process__
  - Type: date
  - Description: Method of thawing.