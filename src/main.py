import os
import supervisely as sly
from dotenv import load_dotenv

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
api = sly.Api.from_env()


project_id = sly.env.project_id()
dataset_id = sly.env.dataset_id()

project_meta_json = api.project.get_meta(project_id)
project_meta = sly.ProjectMeta.from_json(data=project_meta_json)

key_id_map = sly.KeyIdMap()

pcd_ep_ann_json = api.pointcloud_episode.annotation.download(dataset_id)

tag_name = "Car"
tag_values = ["car_1", "car_2"]

if not project_meta.tag_metas.has_key(tag_name):
    new_tag_meta = sly.TagMeta(
        tag_name,
        sly.TagValueType.ONEOF_STRING,
        applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
        possible_values=tag_values,
    )
    new_tags_collection = project_meta.tag_metas.add(new_tag_meta)
    new_project_meta = sly.ProjectMeta(
        tag_metas=new_tags_collection, obj_classes=project_meta.obj_classes
    )
    api.project.update_meta(project_id, new_project_meta)
    new_prject_meta_json = api.project.get_meta(project_id)
    new_project_meta = sly.ProjectMeta.from_json(data=new_prject_meta_json)
    new_tag_meta = new_project_meta.tag_metas.get(new_tag_meta.name)
else:
    new_tag_meta = project_meta.tag_metas.get(tag_name)
    if sorted(new_tag_meta.possible_values) != sorted(tag_values):
        sly.logger.warning(
            f"Tag [{new_tag_meta.name}] already exists, but with another values: {new_tag_meta.possible_values}"
        )

project_objects = pcd_ep_ann_json.get("objects")
tag_frames = [0, 26]
created_tag_ids = {}

for object in project_objects:
    if object["classTitle"] == "Car":
        tag_id = api.pointcloud_episode.object.tag.add(
            new_tag_meta.sly_id, object["id"], value="car_1", frame_range=tag_frames
        )
        created_tag_ids[object["id"]] = tag_id

tag_id_to_operate = created_tag_ids.get(project_objects[0]["id"])

api.pointcloud_episode.object.tag.update(tag_id_to_operate, "car_2")

api.pointcloud_episode.object.tag.remove(tag_id_to_operate)
