"""
This script can be used to create a json file with an entry for each card in Fronts.
It pulls the card info from the various csv files in spreadsheets.
In order to get the necessary data, download each sheet from the mark 4 card spreadsheet 
as a csv file, then put those csv files into the spreadsheet folder. This script assumes
that the default name is used for each csv file.
"""

# Import file parsing libraries
import json
import csv

# Import Path for better file system navigation
import pathlib

def cardMaker(line, labels, card_type, faction):
    """
    A helper function that creates and returns a card dictionary
    line: a list of values corresponding to each label
    labels: a list of labels used to identify and name each value in line
    card_type: a string denoting the type of card
    faction: a string denoting the card's faction
    """

    # Create an object that will store the card data
    card = {}
    
    # Add the card's name, type, and faction
    card[labels[0]] = line[0]
    card["Type"] = card_type
    card["Faction"] = faction

    # Add an entry for each other column in labels
    for index, label in enumerate(labels[1:]):
        card[label] = line[index + 1]
    
    # return the card dictionary
    return card


def main():
    """The main file is executed when the file is run. It creates a json object with card data using
    the csv files pulled from the master spreadsheet on google drive"""
    # Create a dictionary to store the card information. This will be dumped as a json file.
    output_dict = {"cards" : []}

    # Loop through each spreadsheet, parsing the data and adding it to output_dict
    for file in pathlib.Path("Spreadsheets").resolve().glob("*.csv"): # Iterates through each csv file in Spreadsheets
        # Read the csv into a 2d list, splitting by line and by column
        with open(file, "r", newline='') as sheet:
            sheet_reader = csv.reader(sheet)
            lines = [line for line in sheet_reader]

        # Remove empty lines
        lines = list(filter(lambda line: any(col for col in line), lines)) # any statement returns True if any str in line is not empty

        # Extract the faction from the filename, assuming default filenames for each sheet
        faction = str(file)[str(file).find("Mark 4 Cards -") + 15:-4]

        # Iterate through the file, keeping track of what kind of card we are working on and the corresponding column lables
        card_type = ""
        labels = []
        label_update = False # This value is used to determine if labels should be updated after a card type change

        for line in lines:
            if not line[1]: # Some of the sheets have trailing notes. This line ensures that those notes aren't turned into entries
                continue
            elif label_update: # Check if we need to update the labels
                labels = list(filter(lambda label: label, line)) # remove any empty strings from the labels
                label_update = False
                continue
            else:
                # Check if we have reached the next type of card
                match line[0]:
                    # If the line matches any of these cases, move to the correct card type and prepare to update labels
                    case "Leaders":
                        card_type = "Leader"
                        label_update = True
                        continue
                    case "Combatants":
                        card_type = "Combatant"
                        label_update = True
                        continue
                    case "Operations":
                        card_type = "Operation"
                        label_update = True
                        continue
                    case "Assets":
                        card_type = "Asset"
                        label_update = True
                        continue
                    case _:
                        # create and add a card entry to the output
                        output_dict["cards"].append(cardMaker(line, labels, card_type, faction))
    
    # Output the final json object to the database folder
    with open(pathlib.Path("../../Database/Card_Database.json").resolve(), "w") as output:
        output.write(json.dumps(output_dict, indent=True))
    

if __name__ == "__main__":
    main()