import os, platform, shutil, zipfile
import pathlib
path_to_folder = pathlib.Path(__file__).parent.resolve()
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def find_pssm_missing_proteins(set_proteins_fasta, pssm_dir):
    set_proteins_pssm = set()
    for file in os.listdir(pssm_dir):
        protein_id = file.split(".")[0]
        set_proteins_pssm.add(protein_id)
    return list(set_proteins_fasta - set_proteins_pssm)


def read_fasta_to_dict(input_dir, fasta_file, place_protein_id):
    fasta_dict = dict()
    sequence = ""
    prot_id = ""
    with open("{}/{}.fasta".format(input_dir, fasta_file), "r") as fp:
        for line in fp:
            if line[0] == '>':
                if prot_id != "":
                    fasta_dict[prot_id] = sequence
                prot_id = line.strip().split("|")[place_protein_id]
                if place_protein_id == 0:
                    prot_id = prot_id[1:]
                if prot_id not in fasta_dict:
                    sequence = ""
                    fasta_dict[prot_id] = ""
            else:
                sequence += line.strip()
        fasta_dict[prot_id] = sequence
    fp.close()
    return fasta_dict

def form_single_fasta_files(list_proteins_no_pssm, fasta_dict):
    path_single_fastas = "{}/temp_folder/single_fastas".format(path_to_folder)

    print(path_single_fastas)
    if os.path.isdir(path_single_fastas) == False:
        os.mkdir(path_single_fastas)

    for prot_id in list_proteins_no_pssm:
        fw = open("{}/{}.fasta".format(path_single_fastas, prot_id), "w")
        fw.write(">sp|{}\n{}\n".format(prot_id, fasta_dict[prot_id]))
        fw.close()


def form_missing_pssm_files(pssm_dir):

    path_single_fastas = "{}/temp_folder/single_fastas".format(path_to_folder)
    path_blast = "{}/ncbi-blast".format(path_to_folder)

    for filename in os.listdir(path_single_fastas):
        prot_id = filename.split(".")[0].strip()
        single_fasta_prot = "{}/{}".format(path_single_fastas, filename)
        pssmfile = "{}/{}.pssm".format(pssm_dir, prot_id)

        if ("Linux" in str(platform.platform())):
            os.system("{}/psiblast -db {}/uniref50_db/uniref50.blastdb -evalue 0.001 -query {} "
                      "-out_ascii_pssm {}  -out {}/outfile -num_iterations 3 -comp_based_stats 1" \
                      .format(path_blast, path_blast, single_fasta_prot, pssmfile, path_blast))
        elif ("Darwin" in str(platform.platform())):
            os.system("{}/psiblastMAC -db {}/uniref50_db/uniref50.blastdb -evalue 0.001 -query {} "
                      "-out_ascii_pssm {}  -out {}/outfile -num_iterations 3 -comp_based_stats 1" \
                      .format(path_blast, path_blast, single_fasta_prot, pssmfile, path_blast))
    try:
        shutil.rmtree(path_single_fastas)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

def copy_pssms(fasta_dict):
    import requests
    for prot_id in fasta_dict:
        # Define the remote file to retrieve
        remote_url = 'https://slpred.kansil.org/swissprot_pssms/{}.pssm'.format(prot_id)
        # Define the local filename to save data
        local_file = '{}/pssm_files/{}.pssm'.format(path_to_folder, prot_id)
        # Make http request for remote file data
        data = requests.get(remote_url)
        try:
            data.raise_for_status()
            with open(local_file, 'wb') as file:
                file.write(data.content)
        except requests.exceptions.HTTPError:
            continue

            
def copy_form_pssm_matrices(fasta_dict):
    pssm_dir = "{}/pssm_files".format(path_to_folder)
    list_proteins_no_pssm1 = find_pssm_missing_proteins(set(fasta_dict.keys()), pssm_dir)
    if len(list_proteins_no_pssm1) != 0:
        copy_pssms(list_proteins_no_pssm1)
    list_proteins_no_pssm2 = find_pssm_missing_proteins(set(fasta_dict.keys()), pssm_dir)
    if len(list_proteins_no_pssm2) != 0:
        form_single_fasta_files(list_proteins_no_pssm2, fasta_dict)
        form_missing_pssm_files(pssm_dir)


def edit_extracted_features_POSSUM(temp_output_file, output_file, fasta_dict):
    with open(temp_output_file, 'r') as fp:
        fw = open(output_file, 'w')
        for line, prot_id in zip(fp, fasta_dict):
           fw.write('{}\t{}\n'.format(prot_id, line.strip().replace(',', '\t')))
        fw.close()
    fp.close()
    os.remove(temp_output_file)

def edit_extracted_features_iFeature(temp_output_file, output_file, place_protein_id):
    with open(temp_output_file, 'r') as fp:
        fw = open(output_file, 'w')
        for line in fp:
            if line[0] == '#':
                continue
            else:
                line_split = line.strip().split('\t')
                protein_id = line_split[0].split('|')[place_protein_id]
                fw.write(protein_id)
                for feature in line_split[1:]:
                    fw.write('\t{}'.format(feature))
                fw.write('\n')
        fw.close()
    fp.close()
    os.remove(temp_output_file)