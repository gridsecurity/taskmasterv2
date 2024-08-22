from .conn import db
from datetime import datetime
from bson import ObjectId

class Tasks:
    def __init__(self, id=None, num=None):
        if id:
            self.task = db.tasks.find_one({"_id": ObjectId(id)})
        if num:
            self.task = db.tasks.find_one({"num"})
        if self.task == None:
            raise Exception("No task found")

    def update_task(self, key, value, username):
        db.tasks.update_one({"_id": self.task["_id"]}, {"$set": {key: value}})
        self.insert_task_notes(username, "Updated {} to {}".format(key, value), "updates")
        if key == "status" and value == "complete":
            # check open tasks in workflow
            workflow = db.workflows.find_one({"_id": ObjectId(self.task["workflow_id"])})
            # more than 1 task group and not last index
            if len(workflow["task_groups"]) > 1 and len(workflow["task_groups"]) > workflow["task_group_index"] + 1:
                # get task group index tasks
                open_tasks = list(db.tasks.find({"task_group_id": workflow["task_groups"][workflow["task_group_index"]], "status": {"$ne": "complete"}}))
                if len(open_tasks) == 0:
                    # move index
                    db.workflows.update_one({"_id": workflow["_id"]}, {"$set": {"task_group_index": workflow["task_group_index"] + 1}})

    def insert_task_notes(self, username, notes, type):
        db.taskNotes.insert_one({
            "taskId": str(self.task["_id"]),
            "date": datetime.timestamp(datetime.today()),
            "username": username,
            "notes": notes,
            "type": type
        })
