---
description: How to create and add tags to Point Cloud Episode annotation objects and frames
---

# **Tags on PCD Episodes annotation objects and frames**

## **Introduction**

In this tutorial, you will learn how to create new tags and assign them to selected annotation objects or frames (with these objects) in Point Cloud Episodes using the Supervisely SDK.

Supervisely supports different types of tags:

- NONE
- ANY_NUMBER
- ANY_STRING
- ONEOF_STRING

You can find all the information about those types in the [Tags in Annotations](https://developer.supervise.ly/api-references/supervisely-annotation-json-format/tags) section and [SDK](https://supervisely.readthedocs.io/en/latest/sdk/supervisely.annotation.tag_meta.TagMeta.html) documentation.

You can learn more about working with Point Cloud Episodes (PCE) using [Supervisely SDK](https://developer.supervise.ly/getting-started/python-sdk-tutorials/point-clouds-and-episodes) and what [Annotations for PCE](https://developer.supervise.ly/api-references/supervisely-annotation-json-format/point-cloud-episodes) are.

{% hint style="info" %}
Everything you need to reproduce [this tutorial is on GitHub](https://github.com/supervisely-ecosystem/add-tag-to-pcd-ep-objects): source code, Visual Studio Code configuration, and a shell script for creating virtual env.
{% endhint %}

## **How to debug this tutorial**

**Step 1.** Prepare `~/supervisely.env` file with credentials. [Learn more here.](../basics-of-authentication.md#use-.env-file-recommended)

**Step 2.** Clone [repository](https://github.com/supervisely-ecosystem/add-tag-to-pce-objects) with source code and create [Virtual Environment](https://docs.python.org/3/library/venv.html).

```bash
git clone https://github.com/supervisely-ecosystem/add-tag-to-pce-objects
cd add-tag-to-pce-objects
./create_venv.sh
```

**Step 3.** Open repository directory in Visual Studio Code.

```bash
code -r .
```

**Step 4.** Get, for example, [Demo KITTI pointcloud episodes annotated](https://app.supervise.ly/ecosystem/projects/demo-kitti-3d-episodes-annotated) project from Ecosystem.

<img width="1280" src="https://user-images.githubusercontent.com/57998637/231194451-e8797293-0317-4168-a165-7bd59d5b72f3.gif">

Project classes after Demo initialization

<img width="1280" alt="classes" src="https://user-images.githubusercontent.com/57998637/231448142-edf8b36a-1699-4633-856c-440c7789e0f7.png">

Project tags metadata after Demo initialization. This data is empty.

<img width="1280" alt="empty_tags" src="https://user-images.githubusercontent.com/57998637/231447574-fc4002cc-3e0e-45e0-9a3c-e8c8ccd04db8.png">

Visualization in Labeling Tool before we add tags

<img width="1280" alt="tool_before" src="https://user-images.githubusercontent.com/57998637/231228482-b8ef1445-b1f1-40ca-a58b-f2fcac7be822.png">

**Step 5.** Change Workspace ID in `local.env` file by copying the ID from the context menu of the workspace. Do the same for Project ID and Dataset ID .

```python
WORKSPACE_ID=82841  # ⬅️ change value
PROJECT_ID=239385  # ⬅️ change value
DATASET_ID=774629  # ⬅️ change value
```

<img  width="600" src="https://user-images.githubusercontent.com/57998637/231221251-3dfc1a56-b851-4542-be5b-d82b2ef14176.gif">

**Step 6.** Start debugging `src/main.py`

<img width="1280" src="https://user-images.githubusercontent.com/57998637/231476859-244b009d-a936-4be4-b662-c78e8bfc0fb9.gif">

## **Python Code**

### **Import libraries**

```python
import os
import supervisely as sly
from dotenv import load_dotenv
from supervisely.pointcloud_annotation.pointcloud_episode_tag_collection import (
    PointcloudEpisodeTagCollection,
)
```

### **Init API client**

Init `api` for communicating with Supervisely Instance. First, we load environment variables with credentials, Project and Dataset IDs:

```python
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
api = sly.Api.from_env()
```

With next lines we will get values from `local.env`.

```python
PROJECT_ID = sly.env.project_id()
DATASET_ID = sly.env.dataset_id()
```

By using these IDs, we can retrieve the project metadata and annotations, and define the values needed for the following operations.

```python
PROJECT_META_JSON = api.project.get_meta(PROJECT_ID)
PROJECT_META = sly.ProjectMeta.from_json(data=PROJECT_META_JSON)

key_id_map = sly.KeyIdMap()

pcd_entities = api.pointcloud_episode.get_list(DATASET_ID)
pcd_entity_id = pcd_entities[0][0]  # first entity id
pcd_ep_ann_json = api.pointcloud_episode.annotation.download(DATASET_ID)
pcd_ep_ann = sly.PointcloudEpisodeAnnotation.from_json(
    data=pcd_ep_ann_json, project_meta=PROJECT_META, key_id_map=key_id_map
)
project_classes = PROJECT_META.obj_classes
project_tag_metas = PROJECT_META.tag_metas
```

### **Create new tag metadata**

To create a new tag, you need to first define a tag metadata. This includes specifying the tag name, type, the objects to which it can be added, and the possible values. This base information will be used to create the actual tags.

```python
new_tag_meta = sly.TagMeta(
    "Tram",
    sly.TagValueType.ONEOF_STRING,
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    possible_values=["city", "suburb"],
)
```

### **Recreate the source project metadata with new tag metadata**

If a tag metadata with the same name already exists in the project metadata, this step will be skipped.

```python
existing_tag_meta = project_tag_metas.get(new_tag_meta.name)
if existing_tag_meta is None:
    new_tags_collection = project_tag_metas.add(new_tag_meta)
    new_project_meta = sly.ProjectMeta(tag_metas=new_tags_collection, obj_classes=project_classes)
    api.project.update_meta(PROJECT_ID, new_project_meta)
else:
    new_tag_meta = existing_tag_meta
```

New tag metadatas added

<img width="1280" alt="tags_meta" src="https://user-images.githubusercontent.com/57998637/231448616-b81d7f51-bd37-40d8-9caa-87a9207e43b9.png">

### **Create new tag with value**

You can create a tag using the previously created tag metadata, which can have a value and can be assigned to the defined frames. Once you have created the new tag, you can then create a tag Collection with the new tag. This will enable you to recreate certain Objects but with the new tag.

```python
new_tag = sly.PointcloudEpisodeTag(
    meta=new_tag_meta,
    value="suburb",
)
new_tag_collection = PointcloudEpisodeTagCollection([new_tag])
```

If you want to add a tag to frames, you can define the `frame_range` argument.

```python
new_tag = sly.PointcloudEpisodeTag(
    meta=new_tag_meta,
    value="suburb",
    frame_range=[12, 13] # this one
)
```

### **Recreate all objects that meet the requirements**

All objects that belong to the "Tram" class will be processed with a new tag.
In this case, if you try to add tags to the source object using `object.add_tag`, you will receive a duplication error. That's why we recreate the object with only the new tags for further updating of annotations.

```python
new_objects_list = []

for object in pcd_ep_ann.objects:
    if object.obj_class.name == "Tram":
        new_obj = object.clone(tags=new_tag_collection)
        new_objects_list.append(new_obj)
```

If you want to skip objects that already have a particular tag, you should retrieve all the tags for that object and check if the desired tag already exists. If it does, then you can skip that object and move on to the next one.

```python
for object in pcd_ep_ann.objects:
    object_tags = object.tags.items() # this one
    has_this_tag = any(tag.name == new_tag.name for tag in object_tags) # this one
    if object.obj_class.name == "Tram" and not has_this_tag: # this one
        new_obj = object.clone(tags=new_tag_collection)
        new_objects_list.append(new_obj)
```

### **Update annotations**

To update the current annotations in PCE, you need to first create a new annotation based on the original. This new annotation should not overwrite all the information, but only the information that needs to be updated.

```python
new_pcd_ann = pcd_ep_ann.clone(objects=new_objects_list)

api.pointcloud_episode.tag.append_to_objects(
    entity_id=pcd_entity_id,
    project_id=PROJECT_ID,
    objects=new_pcd_ann.objects,
    key_id_map=key_id_map,
)
```

Visualization in Labeling Tool with new tags

<img width="1280" alt="tool_after" src="https://user-images.githubusercontent.com/57998637/231228485-67d1f919-d5b5-4647-b7e4-e8389f0743b2.png">
