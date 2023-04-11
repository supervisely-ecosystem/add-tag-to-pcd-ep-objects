---
description: How to create and add tags to Point Cloud Episode objects and frames
---

# **Tags for objects and frames**

## **Introduction**

In this tutorial, you will learn how to create new tags and assign them to selected objects or frames (with these objects) in Point Cloud Episodes using the Supervisely SDK.

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

**Step 2.** Clone [repository](https://github.com/supervisely-ecosystem/add-tag-to-pce-objects) with source code and demo data and create [Virtual Environment](https://docs.python.org/3/library/venv.html).

```bash
git clone https://github.com/supervisely-ecosystem/add-tag-to-pce-objects
cd add-tag-to-pce-objects
./create_venv.sh
```

**Step 3.** Open repository directory in Visual Studio Code.&#x20;

```bash
code -r .
```

**Step 4.** Get [Demo KITTI pointcloud episodes annotated](https://app.supervise.ly/ecosystem/projects/demo-kitti-3d-episodes-annotated) project from Ecosystem:

<img src=https://user-images.githubusercontent.com/57998637/231194451-e8797293-0317-4168-a165-7bd59d5b72f3.gif width="1918">

**Step 5.** Change Workspace ID in `local.env` file by copying the ID from the context menu of the workspace. Do the same for Project ID and Dataset ID .

```python
WORKSPACE_ID=82841  # ⬅️ change value
PROJECT_ID=239385  # ⬅️ change value
DATASET_ID=774629  # ⬅️ change value
```

<img src=https://user-images.githubusercontent.com/57998637/231221251-3dfc1a56-b851-4542-be5b-d82b2ef14176.gif width="600">

**Step 6.** Start debugging `src/main.py`

<img src=https://user-images.githubusercontent.com/57998637/231219726-f9aa48b3-4460-4523-8bb4-c62f57419c0d.gif width="1906">

## **Python Code**

### **Import libraries**

```python
import os
import supervisely as sly
from dotenv import load_dotenv
from supervisely.collection.key_indexed_collection import DuplicateKeyError
from supervisely.pointcloud_annotation.pointcloud_episode_tag_collection import (
    PointcloudEpisodeTagCollection,
)
from supervisely.pointcloud_annotation.pointcloud_object_collection import (
    PointcloudObjectCollection,
)
```

### **Init API client**

Init api for communicating with Supervisely Instance. First, we load environment variables with credentials, Workspace, Project and Dataset IDs:

```python
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
api = sly.Api.from_env()
```

With next lines we will get values from `local.env`.

```python
PROJECT_ID = sly.env.project_id(False)
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

### **Create new TagMeta**

To create a new Tag, you need to first define a TagMeta. This includes specifying the Tag name, type, the objects to which it can be added, and the possible values. This base information will be used to create the actual Tags.

```python
new_tag_meta = sly.TagMeta(
    "Tram",
    sly.TagValueType.ONEOF_STRING,
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    possible_values=["city", "suburb"],
)
```

### **Update current Project Meta with new TagMeta**

If a TagMeta with the same name already exists in the project metadata, this step will be skipped.

```python
try:
    new_tags_collection = project_tag_metas.add(new_tag_meta)
    new_project_meta = sly.ProjectMeta(tag_metas=new_tags_collection, obj_classes=project_classes)
    api.project.update_meta(PROJECT_ID, new_project_meta)
except DuplicateKeyError:
    sly.logger.warning(f"New tag ['{new_tag_meta.name}'] already exists in project metadata")
    new_tag_meta = project_tag_metas.get(new_tag_meta.name)
```

### **Create new Tag with value**

You can create a Tag using the previously created TagMeta, which can have a value and can be assigned to the defined frames. Once you have created the new Tag, you can then create a Tag Collection with the new Tag. This will enable you to recreate certain Objects but with the new Tag.

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

### **Recreate all Objects that meet the requirements**

All objects that belong to the "Tram" class will be processed with a new Tag.

```python
new_objects_list = []

for object in pcd_ep_ann.objects:
    if object.obj_class.name == "Tram":
        new_obj = object.clone(tags=new_tag_collection)
        new_objects_list.append(new_obj)
```

If you want to skip Objects that already have a particular Tag, you should retrieve all the Tags for that Object and check if the desired Tag already exists. If it does, then you can skip that Object and move on to the next one.

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

## **Visualization in 3D EPISODES LABELING TOOLBOX**

### Project Classes after Demo initialization

<img width="1280" alt="classes" src="https://user-images.githubusercontent.com/57998637/231228488-b0060662-a9ef-452d-b851-85f796ede2d7.png">

### Visualization in Labeling Tool before we add Tags

<img width="1280" alt="tool_before" src="https://user-images.githubusercontent.com/57998637/231228482-b8ef1445-b1f1-40ca-a58b-f2fcac7be822.png">

### New Tags Metadata added

<img width="1280" alt="tags_meta" src="https://user-images.githubusercontent.com/57998637/231228479-6396c0f7-435f-44b0-862d-72e545210be1.png">

### Visualization in Labeling Tool with new Tags

<img width="1280" alt="tool_after" src="https://user-images.githubusercontent.com/57998637/231228485-67d1f919-d5b5-4647-b7e4-e8389f0743b2.png">
