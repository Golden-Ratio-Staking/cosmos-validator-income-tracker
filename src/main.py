'''
Logic:

- Every 60 minutes, query all validators (those who are bonded).
  - Save to cache

Loop through validators & query their commission amounts in terms of ATOM (not uatom).
Save this to a MongoDB collection or redis hset with their amount. (This way we can do a chart of their earnings over time every 1 hour)

Show current total value in USD based on coingecko price
'''
import os, time, json

from dotenv import load_dotenv
from MongoHelper import MongoHelper
from CosmosEndpoints import getOutstandingCommissionRewards, getLatestValidatorSet, getValidatorSlashes


load_dotenv()
m = MongoHelper(uri=os.getenv('MONGODB_URI'))
db = os.getenv('MONGO_DB_NAME')
# print(m.get_databases())


def main():
    addr = "cosmosvaloper1qs8tnw2t8l6amtzvdemnnsq9dzk0ag0z52uzay"
    # takeValidatorSnapshot(addr)

    # CACHE: Save validators to file
    # values = getLatestValidatorSet()
    # with open('validators.json', 'w') as f:
    #   json.dump(getLatestValidatorSet(), f, indent=4)

    # read JSON from validators.json
    # with open('validators.json') as f:
    #     validators = dict(json.load(f))
    # takeValidatorSnapshot(list(validators.keys()))
    # exit()

    
    commissions = dict(query_validator_commission_held_over_time(addr))
    
    import operator
    # sort commissions by their key which is an epoch time
    commissions = sorted(commissions.items(), key=operator.itemgetter(1), reverse=False) # newest time to oldest
    lastCommission, lastTime, isFirst = -1, -1, False

    for comm in commissions:
        t, amt = comm
        # print(t, amt)

        # handles first time & amount in the database as the initial gage
        if lastCommission == -1:
            lastCommission = amt
            # print("Initial commission:", amt)
            isFirst = True
        if lastTime == -1:
            lastTime = t
            # print("Initial time:", t)
            isFirst = True

        if isFirst:
            isFirst = False
            continue

        # subtract amt from last commission, and print the time difference
        print(f"\nBetween {epochTimeToHumanReadable(lastTime)} & {epochTimeToHumanReadable(t)}")
        print(f"in {int(t)-int(lastTime)} Seconds they made {amt-lastCommission} ATOM")

        # update values for the next run    
        lastCommission, lastTime = amt, t
        
        

    pass


def epochTimeToHumanReadable(epoch: str):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(epoch)))


def getDocuments():
    '''Get mongodb documents from a collection in order based on the time field (epoch)'''
    # latest documents first
    documents = m.client[db]['atom'].find().sort(key_or_list='time', direction=-1)
    # for doc in documents:
    #   epoch = doc.get("time")
    #   commissions = doc.get("commissions")
    #   print(epoch, commissions, "\n'")
    # if time is older than 1 day, we move to the 1 day collection I guess?
    return documents

# ----------------------------------------------------------------------

def getAllValidators(fromCacheIfThere=True):
    pass



def takeValidatorSnapshot(validatorOps):
  # loops through all validators & snapshots their current comission
  
  # We could save every 1 hour in "hourly" section. Then have a "daily" as well? still in epoch time?
  # So I guess on hour 23 we move the last hour from hourly to daily collection.
  # for now we just do it every hour

  # validators = getLatestValidatorSet()
  for idx, val in enumerate(validatorOps):
    
    pastData = m.find_one(db, 'atom', {'validator': val})
    newData = {str(int(time.time())): getOutstandingCommissionRewards(val).get("atom")}

    if pastData is None:
      # they never had a snapshot before
      newData = {"validator": val, "values": newData}
    else:
      # they have a snapshot before
      pastData = dict(pastData.get("values"))
      pastData.update(newData) # appends the new current time -> the document
      updatedData = pastData
      newData = {"validator": val, "values": updatedData} # adds the new time & held token to the valoper

    # in the future we will just update it, this works for now
    m.delete_one(db, 'atom', {'validator': val})
    m.insert(db, 'atom', newData)


    # m.insert(db, collectionName="atom", values=data)  
    if idx == 5:
      break


def query_validator_commission_held_over_time(valop):
    doc = m.find_one(db, 'atom', {'validator': valop})
    if doc is None:
        return None
    else:
        return doc.get("values")


  
    





if __name__ == '__main__':
    main()